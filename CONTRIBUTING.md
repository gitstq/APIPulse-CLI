# Contributing to APIPulse-CLI 🤝

Thank you for your interest in contributing to APIPulse-CLI! This document provides guidelines for contributing to the project.

## 📋 How to Contribute

### Reporting Bugs 🐛
1. Check if the issue already exists in the [Issues](https://github.com/gitstq/APIPulse-CLI/issues) section
2. If not, create a new issue with:
   - Clear description of the bug
   - Steps to reproduce
   - Expected vs actual behavior
   - Environment details (OS, Python version)
   - Error logs or screenshots if applicable

### Suggesting Features 💡
1. Open an issue with the `[Feature Request]` label
2. Describe the proposed feature and its use case
3. Explain how it would benefit users

### Submitting Code Changes 📝

#### Development Setup
```bash
# Clone the repository
git clone https://github.com/gitstq/APIPulse-CLI.git
cd APIPulse-CLI

# Install in development mode
pip install -e ".[dev]"

# Run tests
python -m pytest tests/ -v
```

#### Code Standards
- Follow PEP 8 style guidelines
- Add docstrings to all public functions and classes
- Write unit tests for new features
- Keep the zero-dependency philosophy — only use Python stdlib

#### Commit Message Format
Follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:
- `feat: add new feature`
- `fix: fix a bug`
- `docs: update documentation`
- `refactor: code refactoring`
- `test: add/update tests`
- `chore: maintenance tasks`

#### Pull Request Process
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Make your changes and commit
4. Push to your fork (`git push origin feature/your-feature`)
5. Open a Pull Request against the `main` branch
6. Ensure all tests pass

## 📄 License

By contributing, you agree that your contributions will be licensed under the MIT License.
