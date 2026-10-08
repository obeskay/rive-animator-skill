# Contributing to Rive Animator

We welcome contributions of new recipes, framework wiring adapters, converter improvements, and bug fixes!

## Adding a Recipe

1. Create a directory in `examples/<component-name>`:
   - `rive.yaml` with `name: <component-name>`
   - `scene.rml` containing the Artboard, geometry, animations, and State Machine
2. Verify and build with the Rive CLI:
   ```bash
   rive examples/<component-name> --verify
   rive examples/<component-name> --once
   ```
3. Run the linter:
   ```bash
   python3 scripts/rive_lint.py examples/<component-name>/build/<component-name>.riv
   ```
4. Run the test suite:
   ```bash
   python3 -m unittest discover -s tests -v
   ```

## Rules of Thumb

- **Standard Library Only:** Scripts in `scripts/` must run in Python 3.8+ using only Python standard library modules. Zero third-party pip dependencies.
- **Radians for Rotation:** Always verify rotational keyframes use radians (`0` to `6.2831853`), never degrees.
- **Two-way State Machines:** Always ensure states have a clear return transition so the component never latches or freezes.
- **Verified Before Shipped:** Never commit a recipe that hasn't been verified with `--verify`.
