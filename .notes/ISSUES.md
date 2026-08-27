# Open issues

- `telegram/build.py` sets `topBarBg` twice with different values (`title_bar`
  in the chrome block, `panel` in the compose-bar block), so the emitted
  palette carries the key twice and which one Telegram keeps is undefined here.

- `catcad/build.py` interpolates `ink_dim` between `elem_active` and
  `line_number`, and both now resolve to `gray_44`, so the role collapses onto
  `chip_active` and `cube_high` instead of sitting in a gap.
