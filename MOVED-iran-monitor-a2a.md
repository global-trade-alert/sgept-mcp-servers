# iran-monitor-a2a moved

The `iran-monitor-api/` and `a2a-protocol/` packages that previously lived here
have been extracted into their own standalone repository:

**https://github.com/global-trade-alert/iran-monitor-a2a**

Locally:
```
~/Documents/GitHub/jf-private/jf-dev/sgept-dev/iran-monitor-a2a/
```

The Python package was renamed `iran-monitor-api` → `iran-monitor-a2a` in the
process. Imports go from `from iran_monitor_api.X import Y` to
`from iran_monitor_a2a.X import Y`.

The `a2a-protocol` package lives as a sibling subdirectory inside the new
repo. It is consumed by iran-monitor-a2a via a uv path-dependency
(`./a2a-protocol`). When a second consumer ships (e.g. gta-a2a), the
`a2a-protocol/` subtree can be extracted to its own repo with
`git subtree split`.

JCC-974 documents the move.
