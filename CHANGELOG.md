# Changelog

All notable changes to the Slack Foundation Models Bot project.

## [1.0.0] - 2025-10-23

### Major Release - Production Ready

#### Added
- **Dashboard with Left Navigation** - Clean sidebar with 6 sections (Overview, Features, Model Usage, User Guide, Technical Details, System Info)
- **Service Principal Investigation** - Documented findings on service principal authentication limitations
- **Archive Structure** - Organized old experimental and backup files into `archive/` directory
- **Updated OpenAI Library** - Fixed compatibility issues (v1.3.0 → v1.12.0+)

#### Features
- Socket Mode integration for instant Slack responses
- 7 Databricks Foundation Models support:
  - Llama 4 Maverick (databricks-llama-4-maverick)
  - Claude Opus 4.1 (databricks-claude-opus-4-1)
  - Claude Sonnet 4.5 (databricks-claude-sonnet-4-5)
  - Llama 3.1 405B (databricks-meta-llama-3-1-405b-instruct)
  - Llama 3.3 70B (databricks-meta-llama-3-3-70b-instruct)
  - Llama 3.1 8B (databricks-meta-llama-3-1-8b-instruct)
  - GPT OSS 120B (databricks-gpt-oss-120b)
- Real-time metrics tracking (requests, tokens, users, conversations)
- Per-thread conversation history
- FastAPI dashboard with auto-refresh
- Model switching per user

#### Deployment History
- **01f0b04864541f43a028e249c1bdd66c** (2025-10-23 19:42) - Repository cleanup deployment
- **01f0b02e3f00183d89120d665f5d782e** (2025-10-23 16:35) - Fixed OpenAI library version
- **01f0af9524f01430a81faa1fac03038e** (2025-10-22 22:19) - Auto-restart after testing
- **01f0af9413481383becbcac0dc6bd756** (2025-10-22 22:11) - Service principal test attempt 2
- **01f0af9342f710869a4669efce26a7b5** (2025-10-22 22:05) - Service principal test app created
- **01f0af83ef6011f1acfd0dc33cedb52b** (2025-10-22 20:16) - Dashboard with left navigation panel
- **01f0af8307dd19dfb6aee7b4838939bc** (2025-10-22 20:09) - System information section added

#### Technical Details
- **Authentication**: Personal Access Token (PAT) required for foundation models
- **Service Principal Auth**: Tested and confirmed NOT supported for foundation model endpoints
- **Deployment**: Databricks Apps via Socket Mode
- **Architecture**: FastAPI + Socket Mode in single app, threading for dual servers

#### Documentation
- README.md - Main project documentation
- DATABRICKS_APP_DEPLOYMENT.md - Deployment guide
- SLACK_SETUP_GUIDE.md - Slack app configuration
- SERVICE_PRINCIPAL_INVESTIGATION.md - Authentication research findings

---

## [0.9.0] - 2025-10-22

### Pre-release - Service Principal Testing

#### Added
- Test app for service principal authentication (`slack-bot-sp-test`)
- Investigation into WorkspaceClient auto-authentication
- Multiple API endpoint format tests

#### Key Findings
- Service principal tokens work for WorkspaceClient initialization
- Service principal tokens DO NOT work for foundation model serving endpoints
- Foundation models require user PATs, not service principal tokens

---

## [0.8.0] - 2025-10-21

### Beta - Databricks Apps Deployment

#### Added
- Initial Databricks Apps deployment
- Socket Mode integration
- Dashboard with metrics
- Token management via environment variables

#### Changed
- Migrated from webhooks to Socket Mode
- Hardcoded tokens in app.yml (secret scope issues)

#### Fixed
- OAuth blocking webhook endpoints
- Socket Mode enable requirement
- Double `https://` in URL construction

---

## Archive

Previous experimental versions have been archived in:
- `archive/experimental/` - Local development experiments
- `archive/deployed-backups/` - Deployment history backups  
- `archive/docs/` - Outdated documentation

See archived files for historical development context.

