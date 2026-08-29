# Open issues

- `tools/render_palette.py` picks whichever font the host machine has, so
  `palette.png` regenerates differently on macOS than on Linux. Every rebuild
  on a different machine rewrites the whole committed image.
- Long swatch labels clip at the cell edge in `palette.png`, for example
  `search_match_active` and `ansi_bright_magenta`.
