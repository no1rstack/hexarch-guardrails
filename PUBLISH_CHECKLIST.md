# PyPI Publication Checklist - hexarch-guardrails v0.1.0

## ✅ Step 1: Licensing Metadata (COMPLETE)

- [x] **LICENSE file exists** at repo root
  - Path: `LICENSE`
  - Type: MIT License
  - Copyright: © 2026 Noir Stack LLC

- [x] **Packaging metadata configured**
  - File: `setup.py`
  - License field: `license="MIT"`
  - License file: `license_files=["LICENSE"]`
  - Verified in dist: `hexarch_guardrails-0.1.0.dist-info/licenses/LICENSE`

- [x] **README includes license section**
  - Location: Bottom of README.md
  - Content: "MIT © Noir Stack LLC" with link to LICENSE

## ✅ Step 2: Package Identity (VERIFIED)

**Package Metadata:**
```
Name: hexarch-guardrails
Version: 0.1.0
Description: Lightweight policy-driven API protection and guardrails library
Author: Noir Stack
Maintainer: Hira
Email: hira@noirstack.com
```

**URLs:**
- Home: https://www.noirstack.com/
- Repository: https://github.com/no1rstack/hexarch-guardrails
- Documentation: https://github.com/no1rstack/hexarch-guardrails#readme

**Python Compatibility:**
- Requires: Python >=3.8
- Tested: 3.8, 3.9, 3.10, 3.11

## 📦 Build Artifacts (READY)

- [x] Source distribution: `dist/hexarch_guardrails-0.1.0.tar.gz`
- [x] Wheel: `dist/hexarch_guardrails-0.1.0-py3-none-any.whl`
- [x] LICENSE included in both packages
- [x] README.md included with proper encoding

## ⚠️ Step 3: TestPyPI Dry Run (RECOMMENDED NEXT)

**Purpose:** Test upload without permanent consequences

**Actions Required:**

1. **Create TestPyPI API token:**
   - Visit: https://test.pypi.org/manage/account/token/
   - Generate new token for hexarch-guardrails
   - Scope: Project (hexarch-guardrails) or Account-wide

2. **Set credentials:**
   ```powershell
   $env:TWINE_USERNAME = "__token__"
   $env:TWINE_PASSWORD = "pypi-AgE..." # Your TestPyPI token
   ```

3. **Upload to TestPyPI:**
   ```powershell
   python -m twine upload --repository testpypi dist/*
   ```

4. **Verify TestPyPI page:**
   - URL: https://test.pypi.org/project/hexarch-guardrails/
   - Check: README renders correctly
   - Check: License badge shows "MIT"
   - Check: Metadata displays properly

5. **Test installation:**
   ```powershell
   # Create clean test environment
   python -m venv test-env
   .\test-env\Scripts\Activate.ps1
   
   # Install from TestPyPI
   pip install --index-url https://test.pypi.org/simple/ hexarch-guardrails
   
   # Verify import
   python -c "from hexarch_guardrails import Guardian; print(Guardian.__doc__)"
   
   # Cleanup
   deactivate
   Remove-Item test-env -Recurse -Force
   ```

**If TestPyPI succeeds → Proceed to Step 4**

## 🚀 Step 4: Real PyPI Publication (IRREVERSIBLE)

**⚠️ WARNING:** This action is permanent. Version 0.1.0 cannot be re-uploaded.

**Pre-flight checks:**
- [ ] TestPyPI upload succeeded
- [ ] Test installation from TestPyPI worked
- [ ] README renders correctly on TestPyPI
- [ ] LICENSE displays properly on TestPyPI
- [ ] Ready to claim `hexarch-guardrails` name permanently

**Actions Required:**

1. **Create PyPI API token:**
   - Visit: https://pypi.org/manage/account/token/
   - Generate new token
   - Scope: Project or Account

2. **Set credentials:**
   ```powershell
   $env:TWINE_USERNAME = "__token__"
   $env:TWINE_PASSWORD = "pypi-AgE..." # Your REAL PyPI token
   ```

3. **Upload to PyPI:**
   ```powershell
   python -m twine upload dist/*
   ```

4. **Expected output:**
   ```
   Uploading distributions to https://upload.pypi.org/legacy/
   Uploading hexarch_guardrails-0.1.0-py3-none-any.whl
   100% ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 15.4/15.4 kB
   Uploading hexarch_guardrails-0.1.0.tar.gz
   100% ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 12.3/12.3 kB
   
   View at: https://pypi.org/project/hexarch-guardrails/0.1.0/
   ```

## ✅ Step 5: Post-Publish Verification (CRITICAL)

**Immediately after upload:**

1. **PyPI project page:**
   - Visit: https://pypi.org/project/hexarch-guardrails/
   - Verify: README displays correctly
   - Verify: License shows "MIT"
   - Verify: Author/Maintainer correct
   - Verify: URLs point to correct repositories

2. **Fresh installation test:**
   ```powershell
   # Clean environment
   python -m venv verify-env
   .\verify-env\Scripts\Activate.ps1
   
   # Install from PyPI
   pip install hexarch-guardrails
   
   # Version check
   python -c "import hexarch_guardrails; print(hexarch_guardrails.__version__)"
   
   # Import test
   python -c "from hexarch_guardrails import Guardian, PolicyViolation; print('OK')"
   
   # Cleanup
   deactivate
   Remove-Item verify-env -Recurse -Force
   ```

3. **Documentation check:**
   - Confirm README renders on PyPI
   - Check LICENSE badge/link works
   - Verify all URLs are clickable

## 📋 Optional Follow-ups (Can be done later)

### Future Version Planning:
- [ ] Add CHANGELOG.md for tracking changes
- [ ] Create GitHub release tags matching PyPI versions
- [ ] Set up GitHub Actions for automated publishing
- [ ] Add security policy (SECURITY.md)

### Package Namespace Management:
- [ ] Reserve related names if planning expansion:
  - `hexarch-cli` (CLI tools)
  - `hexarch-server` (Backend components)
  - `hexarch-react` (React integrations)

### Metadata Enhancements:
- [ ] Add keywords for better discoverability
- [ ] Include code examples in long_description
- [ ] Add badges to README (PyPI version, downloads, license)

## 🔒 Security Considerations

**What this license DOES:**
- ✅ Allows anyone to use, modify, distribute the code
- ✅ Permits commercial use
- ✅ Minimal restrictions (just attribution)

**What this license DOES NOT do:**
- ❌ Open-source the Hexarch product itself
- ❌ Transfer trademark rights
- ❌ Obligate support or warranties
- ❌ Affect other Noir Stack properties

**Scope:** This MIT license applies ONLY to code in the `hexarch-guardrails-py` repository.

## 📊 Known Non-Blocking Issues

**SetuptoolsDeprecationWarning:**
```
License classifiers are deprecated.
Please consider removing the following classifiers in favor of a SPDX license expression:
License :: OSI Approved :: MIT License
```

**Impact:** Advisory only, does not prevent publishing

**Resolution:** Can be fixed in future releases by migrating to `pyproject.toml`

**For now:** Safe to ignore, package will publish successfully

## 🎯 Current Status

**Build Status:** ✅ Complete  
**License Status:** ✅ Complete  
**Metadata Status:** ✅ Verified  
**Ready for:** TestPyPI → Real PyPI

**Next Action:** Run TestPyPI dry run (Step 3)
