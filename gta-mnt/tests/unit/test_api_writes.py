"""Regression tests for the write-side schema-drift fix on add_sector,
add_product, and the new add_product_level (HS8/10/12/14) handler.

All tests run with dry_run=True, which short-circuits before
GTADatabaseClient._get_connection() — no live DB needed.
"""

import pytest
from pydantic import ValidationError

from gta_mnt.api import GTADatabaseClient
from gta_mnt.server import (
    AddSectorInput,
    AddProductInput,
    AddProductLevelInput,
)


@pytest.fixture
def client(tmp_path):
    """Bare client; dry_run=True paths never touch the connection.
    storage is the only optional ctor arg — point it at tmp_path so the
    test never writes outside its sandbox."""
    from gta_mnt.storage import ReviewStorage
    return GTADatabaseClient(storage=ReviewStorage(base_path=str(tmp_path)))


# ----------------------------------------------------------------------
# add_sector
# ----------------------------------------------------------------------


class TestAddSector:
    def test_default_writes_is_investigated_only_zero(self, client):
        result = client.add_sector(intervention_id=1, sector_id=2, dry_run=True)
        assert result['dry_run'] is True
        assert 'is_investigated_only' in result['sql']
        # Order: intervention_id, sector_id, type, is_investigated_only
        assert result['params'] == ['1', '2', 'N', '0']

    def test_investigated_only_true_writes_one(self, client):
        result = client.add_sector(
            intervention_id=1, sector_id=2,
            is_investigated_only=True, dry_run=True,
        )
        assert result['params'][-1] == '1'

    def test_sector_type_override_preserved(self, client):
        result = client.add_sector(
            intervention_id=1, sector_id=2,
            sector_type='A', is_investigated_only=False, dry_run=True,
        )
        assert result['params'][2] == 'A'
        assert result['params'][-1] == '0'


# ----------------------------------------------------------------------
# add_product
# ----------------------------------------------------------------------


class TestAddProduct:
    def test_default_writes_required_columns(self, client):
        result = client.add_product(intervention_id=1, product_id=10, dry_run=True)
        assert result['dry_run'] is True
        # Both new NOT-NULL columns must appear in the INSERT
        assert 'is_investigated_only' in result['sql']
        assert 'type' in result['sql']
        # And type must literally be 'N' (hardcoded, not from caller)
        assert "'N'" not in result['sql']  # value comes through %s placeholder, not literal
        # Position: intervention_id, product_id, is_completely_captured(0),
        # is_in_original(1), is_investigated_only(0), type('N')
        assert result['params'][0] == '1'   # intervention_id
        assert result['params'][1] == '10'  # product_id
        assert result['params'][2] == '0'   # is_completely_captured
        assert result['params'][3] == '1'   # is_in_original
        assert result['params'][4] == '0'   # is_investigated_only default
        assert result['params'][5] == 'N'   # type hardcoded

    def test_investigated_only_flag_threads_through(self, client):
        result = client.add_product(
            intervention_id=1, product_id=10,
            is_investigated_only=True, dry_run=True,
        )
        assert result['params'][4] == '1'

    def test_optional_columns_appended_after_base(self, client):
        result = client.add_product(
            intervention_id=1, product_id=10,
            prior_level='5.0', new_level='25.0', unit_id=1,
            dry_run=True,
        )
        # type stays at position 5; new optionals come AFTER, in order
        assert result['params'][5] == 'N'
        assert '5.0' in result['params']
        assert '25.0' in result['params']

    def test_input_model_forbids_type_field(self):
        # The MCP boundary must not let the caller set `type` — it would
        # bypass the aggregation contract.
        with pytest.raises(ValidationError):
            AddProductInput(intervention_id=1, product_id=10, type='A')


# ----------------------------------------------------------------------
# HS code cleaning helper
# ----------------------------------------------------------------------


class TestCleanHsCode:
    @pytest.mark.parametrize('raw,expected', [
        ('0102.10.20', '01021020'),
        ('0102-10-20', '01021020'),
        ('0102 10 20', '01021020'),
        ('01021020',   '01021020'),
        (' 0102.10.20 ', '01021020'),
        ('9706.90.00', '97069000'),
        # Longer codes — punctuation cleaned, all digits kept
        ('9603.90.80.50', '9603908050'),
    ])
    def test_strips_punctuation_preserves_digits(self, raw, expected):
        assert GTADatabaseClient._clean_hs_code(raw) == expected

    def test_leading_zero_chapter_preserved_in_string(self):
        # Live Bovine, chapter 01 — must keep all 8 characters until
        # post-validation int conversion.
        assert GTADatabaseClient._clean_hs_code('0102.10.20') == '01021020'
        assert len(GTADatabaseClient._clean_hs_code('0102.10.20')) == 8


# ----------------------------------------------------------------------
# add_product_level (HS8 / HS10 / HS12 / HS14)
# ----------------------------------------------------------------------


class TestAddProductLevel:
    def test_level_must_be_in_8_10_12_14(self, client):
        for bad in (6, 7, 9, 11, 13, 15, 0, -1):
            result = client.add_product_level(
                intervention_id=1, level=bad, hs_code='12345678',
                jurisdiction_id=840, action_id=1, dry_run=True,
            )
            assert result['success'] is False
            assert 'level' in result['error'].lower()

    def test_hs_length_must_match_level(self, client):
        # 8-digit code passed with level=10 → error
        result = client.add_product_level(
            intervention_id=1, level=10, hs_code='12345678',
            jurisdiction_id=840, action_id=1, dry_run=True,
        )
        assert result['success'] is False
        assert '10 digits' in result['error']

    def test_punctuated_hs_code_normalizes(self, client):
        result = client.add_product_level(
            intervention_id=1, level=8, hs_code='9706.90.00',
            jurisdiction_id=840, action_id=1, dry_run=True,
        )
        assert result['dry_run'] is True
        assert result['cleaned_hs_code'] == '97069000'
        # Composite per upstream serializer: int(str(97069000) + '840') = 97069000840
        assert result['master_id'] == 97069000840

    def test_master_id_construction_for_leading_zero_chapter(self, client):
        # HS 0102.10.20 (Live Bovine) for Austria (jur 40)
        # Cleaned string: '01021020' (8 chars, validates)
        # int('01021020') = 1021020, then composite = 1021020 followed by '040'
        result = client.add_product_level(
            intervention_id=1, level=8, hs_code='0102.10.20',
            jurisdiction_id=40, action_id=1, dry_run=True,
        )
        assert result['cleaned_hs_code'] == '01021020'
        assert result['master_id'] == 1021020040

    def test_level8_requires_action_id(self, client):
        result = client.add_product_level(
            intervention_id=1, level=8, hs_code='12345678',
            jurisdiction_id=840, dry_run=True,
        )
        assert result['success'] is False
        assert 'action_id' in result['error']

    def test_level10_requires_action_id(self, client):
        result = client.add_product_level(
            intervention_id=1, level=10, hs_code='1234567890',
            jurisdiction_id=840, dry_run=True,
        )
        assert result['success'] is False
        assert 'action_id' in result['error']

    def test_level12_does_not_require_action_id(self, client):
        # 12-digit code, no action_id → still succeeds (different schema)
        result = client.add_product_level(
            intervention_id=1, level=12, hs_code='123456789012',
            jurisdiction_id=840, dry_run=True,
        )
        assert result['dry_run'] is True
        # 14-col schema has no action_id column
        assert 'action_id' not in result['sql']
        assert 'applicability_reason_id' not in result['sql']
        assert 'verification_status_id' not in result['sql']

    def test_level14_does_not_require_action_id(self, client):
        result = client.add_product_level(
            intervention_id=1, level=14, hs_code='12345678901234',
            jurisdiction_id=840, dry_run=True,
        )
        assert result['dry_run'] is True

    def test_level8_sql_contains_required_columns(self, client):
        result = client.add_product_level(
            intervention_id=1, level=8, hs_code='12345678',
            jurisdiction_id=840, action_id=1, dry_run=True,
        )
        sql = result['sql']
        for col in (
            'intervention_id', 'product_level8_id',
            'action_id', 'applicability_reason_id', 'verification_status_id',
            'is_completely_captured', 'is_in_original', 'is_positively_affected',
            'is_tariff_line_official', 'is_investigated_only', 'type',
        ):
            assert col in sql, f"missing column {col} in level8 INSERT"

    def test_target_table_per_level(self, client):
        cases = [
            (8,  'api_intervention_product_level8'),
            (10, 'api_intervention_product_level10'),
            (12, 'api_intervention_product_level12_log'),
            (14, 'api_intervention_product_level14_log'),
        ]
        for level, tbl in cases:
            kw = {'action_id': 1} if level in (8, 10) else {}
            result = client.add_product_level(
                intervention_id=1, level=level,
                hs_code='1' * level, jurisdiction_id=840,
                dry_run=True, **kw,
            )
            assert tbl in result['sql'], f"level {level} should target {tbl}"

    def test_type_always_n_never_settable(self, client):
        # Hardcoded 'N' in the params
        result = client.add_product_level(
            intervention_id=1, level=8, hs_code='12345678',
            jurisdiction_id=840, action_id=1, dry_run=True,
        )
        assert 'N' in result['params']
        # And the Pydantic input model rejects a `type` kwarg outright
        with pytest.raises(ValidationError):
            AddProductLevelInput(
                intervention_id=1, level=8, hs_code='12345678',
                jurisdiction_id=840, action_id=1, type='A',
            )

    def test_optional_value_columns_appear_when_set(self, client):
        result = client.add_product_level(
            intervention_id=1, level=8, hs_code='12345678',
            jurisdiction_id=840, action_id=1,
            prior_value='5.0', new_value='25.0', unit_id=1,
            dry_run=True,
        )
        assert 'prior_value' in result['sql']
        assert 'new_value' in result['sql']
        assert 'unit_id' in result['sql']

    def test_optional_value_columns_absent_when_not_set(self, client):
        result = client.add_product_level(
            intervention_id=1, level=8, hs_code='12345678',
            jurisdiction_id=840, action_id=1, dry_run=True,
        )
        assert 'prior_value' not in result['sql']
        assert 'new_value' not in result['sql']

    def test_input_model_extra_forbid(self):
        with pytest.raises(ValidationError):
            AddProductLevelInput(
                intervention_id=1, level=8, hs_code='12345678',
                jurisdiction_id=840, action_id=1,
                garbage_field='boom',
            )
