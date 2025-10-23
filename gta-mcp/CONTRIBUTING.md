# Contributing to GTA MCP Server

Thank you for your interest in contributing to the GTA MCP Server! This document provides guidelines for contributing to the project.

## Getting Started

### Prerequisites

- Python 3.10 or higher
- [uv](https://github.com/astral-sh/uv) package manager
- GTA API key from SGEPT

### Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/YOUR_USERNAME/gta-mcp.git
   cd gta-mcp
   ```

2. **Install dependencies**
   ```bash
   uv sync
   ```

3. **Set up your API key**
   ```bash
   export GTA_API_KEY='your-api-key-here'
   ```

4. **Test the installation**
   ```bash
   uv run gta-mcp --help
   ```

## Development Workflow

### Making Changes

1. **Create a new branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**
   - Follow the code style guidelines below
   - Add tests if applicable
   - Update documentation if needed

3. **Test your changes**
   ```bash
   # Run basic import test
   uv run python -c "from gta_mcp import server; print('OK')"

   # Test with real API calls
   GTA_API_KEY='your-key' uv run gta-mcp
   ```

4. **Commit your changes**
   ```bash
   git add .
   git commit -m "Brief description of your changes"
   ```

5. **Push and create a Pull Request**
   ```bash
   git push origin feature/your-feature-name
   ```

## Code Style Guidelines

### Python

- **Indentation**: Use **tabs** with indent size 4 (not spaces)
- **Formatting**: Follow PEP-8 style guide
- **Type hints**: Add type hints to all function signatures
- **Docstrings**: Use Google-style docstrings for all public functions

Example:
```python
def search_interventions(
	filters: Dict[str, Any],
	limit: int = 50
) -> List[Dict[str, Any]]:
	"""Search for interventions using filters.

	Args:
		filters: Dictionary of filter parameters
		limit: Maximum number of results to return

	Returns:
		List of intervention dictionaries

	Raises:
		ValueError: If filters are invalid
	"""
	pass
```

### Comments

- Use comments sparingly and only when needed to explain complex logic
- Prefer self-documenting code with clear variable and function names
- Keep comments concise and up-to-date

### File Organization

- Keep files focused on a single responsibility:
  - `api.py` - API client and request handling
  - `models.py` - Pydantic input validation models
  - `formatters.py` - Response formatting (markdown/JSON)
  - `server.py` - MCP server and tool implementations
  - `resources_loader.py` - Resource file loading utilities

## Testing

### Manual Testing

Test your changes with real API calls:

```python
import asyncio
from gta_mcp.api import GTAAPIClient, build_filters

async def test():
    client = GTAAPIClient('your-api-key')
    filters = build_filters({'implementing_jurisdictions': ['USA']})
    results = await client.search_interventions(filters=filters, limit=5)
    print(f"Got {len(results)} results")

asyncio.run(test())
```

### Testing Checklist

Before submitting a PR, ensure:

- [ ] Code follows style guidelines (tabs, type hints, docstrings)
- [ ] All functions have proper error handling
- [ ] New features are documented in README.md
- [ ] Changes don't break existing functionality
- [ ] API calls work with real GTA API

## Documentation

### Updating Documentation

When making changes, update relevant documentation:

- **README.md** - For user-facing features and usage examples
- **Docstrings** - For code-level documentation
- **CHANGELOG.md** - For version history

### Documentation Style

- Use clear, concise language
- Provide code examples where appropriate
- Include links to relevant GTA resources
- Keep formatting consistent with existing docs

## Pull Request Process

1. **Before submitting**:
   - Ensure all tests pass
   - Update documentation
   - Add entry to CHANGELOG.md
   - Rebase on latest main branch

2. **PR Description**:
   - Clearly describe what changes were made and why
   - Link any related issues
   - Include screenshots if UI changes

3. **Review Process**:
   - Maintainers will review your PR
   - Address any feedback or requested changes
   - Once approved, your PR will be merged

## Reporting Issues

### Bug Reports

When reporting bugs, include:

- Clear description of the issue
- Steps to reproduce
- Expected vs. actual behavior
- Python version and environment details
- Relevant error messages or logs

### Feature Requests

For new features, provide:

- Clear description of the proposed feature
- Use case and motivation
- Example of how it would be used
- Any relevant GTA API documentation

## Code of Conduct

### Our Standards

- Be respectful and inclusive
- Welcome diverse perspectives
- Focus on constructive feedback
- Help others learn and grow

### Unacceptable Behavior

- Harassment or discrimination
- Trolling or inflammatory comments
- Publishing private information
- Other unprofessional conduct

## Questions?

If you have questions about contributing:

- Open a GitHub issue with the "question" label
- Check existing issues and documentation
- Contact the maintainers

Thank you for contributing to the GTA MCP Server!
