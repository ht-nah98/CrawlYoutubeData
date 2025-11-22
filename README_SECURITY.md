# 🔒 Security Guidelines

## ⚠️ IMPORTANT: Sensitive Data Protection

This application handles sensitive data including:
- YouTube session cookies
- Account credentials
- Personal configuration files

**NEVER commit these files to Git or push them to GitHub!**

## 🛡️ Protected Files

The following files/directories are automatically ignored by `.gitignore`:

### Configuration Files
- `config.json` - Your account and channel configuration
- `gui/config.json` - GUI settings
- `settings.json` - Application settings
- `.claude/settings.local.json` - Claude AI settings

### Data Files
- `data/` - All data directory contents
- `data/cookies/` - Cookie files (contains session tokens)
- `data/cookies/profile/*.json` - YouTube session cookies

### Profile Files
- Any files in `profile/` or `profiles/` directories

## 📝 Setup Instructions

1. **Copy the example config file:**
   ```bash
   cp config.json.example config.json
   ```

2. **Edit `config.json` with your actual data:**
   - Replace `Account1`, `Account2` with your account names
   - Update channel URLs and video IDs
   - Set correct paths to your cookie files

3. **Add your YouTube cookies:**
   - Place your cookie JSON files in `data/cookies/profile/`
   - Name them according to your config (e.g., `youtube_cookies_YourName.json`)

## 🚨 If You Accidentally Committed Sensitive Data

If you accidentally committed sensitive files:

1. **Immediately revoke/change all credentials:**
   - Log out of all YouTube sessions
   - Change your passwords
   - Revoke any API tokens

2. **Remove from Git history:**
   ```bash
   git filter-branch --force --index-filter \
     "git rm --cached --ignore-unmatch SENSITIVE_FILE" \
     --prune-empty --tag-name-filter cat -- --all
   
   git push origin main --force
   ```

3. **Contact support if the repository was public**

## ✅ Best Practices

1. **Never share your `config.json` or cookie files**
2. **Use `.gitignore` to prevent accidental commits**
3. **Regularly rotate your credentials**
4. **Keep your repository private**
5. **Review commits before pushing**

## 📋 Checklist Before Pushing

- [ ] No `config.json` in commit
- [ ] No files in `data/` directory in commit
- [ ] No cookie files (`.json` in `data/cookies/`)
- [ ] No personal settings files
- [ ] Reviewed `git status` output
- [ ] Confirmed only code files are being committed

---

**Remember:** When in doubt, DON'T commit it! It's easier to add files later than to remove them from Git history.
