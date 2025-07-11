# Collector Charm

A Juju charm for deploying and managing HAProxy data collectors. This charm automatically fetches collector code from GitHub repositories, configures the environment, and manages the collector service lifecycle.

## Architecture

The charm has been refactored into a modular architecture for better maintainability and reusability:

### Module Structure

- **`config.py`** - Configuration validation and management
- **`service_manager.py`** - Systemd service operations (start, stop, restart)
- **`github_client.py`** - GitHub repository management and code fetching
- **`file_manager.py`** - File operations, environment files, and dependencies
- **`templates.py`** - Systemd service and timer templates
- **`charm.py`** - Main charm orchestration

## Features

- ✅ Automated collector deployment from GitHub repositories
- ✅ HAProxy configuration management
- ✅ Systemd service and timer management
- ✅ Environment file generation
- ✅ Dependency installation
- ✅ Configuration validation
- ✅ Service lifecycle management (start, stop, restart, reload)

## Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `collector-name` | string | - | Unique name for the collector instance |
| `haproxy-name` | string | - | HAProxy instance identifier |
| `haproxy-url` | string | - | HAProxy API endpoint URL |
| `haproxy-username` | string | - | HAProxy authentication username |
| `haproxy-password` | string | - | HAProxy authentication password |
| `frequency` | int | 600 | Collection interval in seconds |
| `github-token` | string | - | GitHub personal access token |
| `github-repo` | string | - | GitHub repository URL |
| `release-tag` | string | v1.0.0 | Repository tag/version to fetch |
| `sub-directory` | string | - | Subdirectory in the repository |

## Building the Charm

### Prerequisites

- [Charmcraft](https://juju.is/docs/sdk/install-charmcraft) installed
- Ubuntu 22.04 or compatible environment

### Build Steps

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd charm-deployment-demo/charm
   ```

2. **Install dependencies:**
   ```bash
   sudo snap install charmcraft --classic
   ```

3. **Build the charm:**
   ```bash
   charmcraft pack
   ```

   This will create a `.charm` file in the current directory.

4. **Verify the build:**
   ```bash
   ls -la *.charm
   ```

## Deployment

### Prerequisites

- [Juju](https://juju.is/docs/olm/get-started-with-juju) installed and configured
- A Juju model ready for deployment

### Deploy the Charm

1. **Deploy from local file:**
   ```bash
   juju deploy ./collector-charm_ubuntu-22.04-amd64.charm collector
   ```

2. **Configure the charm:**
   ```bash
   juju config collector \
     collector-name="my-collector" \
     haproxy-name="main-haproxy" \
     haproxy-url="https://haproxy.example.com:8080" \
     haproxy-username="admin" \
     haproxy-password="password" \
     github-token="your-github-token" \
     github-repo="https://github.com/user/collector-repo" \
     release-tag="v1.2.0" \
     sub-directory="haproxy_collector" \
     frequency=300
   ```

3. **Check deployment status:**
   ```bash
   juju status
   ```

### Managing the Service

The charm provides several actions for service management:

```bash
# Start the collector service
juju run collector/0 start

# Stop the collector service  
juju run collector/0 stop

# Restart the collector service
juju run collector/0 restart

# Reload configuration and restart
juju run collector/0 reload
```

### Updating Configuration

To update the configuration:

```bash
juju config collector haproxy-url="https://new-haproxy.example.com:8080"
```

The charm will automatically:
- Validate the new configuration
- Update environment files if needed
- Fetch new collector code if repository settings changed
- Restart the service with new configuration

## Development

### Running Tests

```bash
# Run all tests
tox

# Run specific test types
tox run -e format        # Code formatting
tox run -e lint          # Linting
tox run -e static        # Static type checking
tox run -e unit          # Unit tests
tox run -e integration   # Integration tests
```

### Development Environment

```bash
# Create development environment
tox devenv -e integration
source venv/bin/activate
```

## Monitoring

### Logs

View charm logs:
```bash
juju debug-log --include collector
```

View service logs:
```bash
juju ssh collector/0 'sudo journalctl -u collector.service -f'
```

### Status Monitoring

The charm reports its status through Juju:
- **Active**: Service is running normally
- **Blocked**: Configuration error or service failure
- **Maintenance**: Performing updates or restarts

## Troubleshooting

### Common Issues

1. **Configuration Validation Errors:**
   - Check all required fields are provided
   - Verify URL formats (must start with http/https)
   - Ensure GitHub token has proper permissions

2. **GitHub Access Issues:**
   - Verify GitHub token is valid and has repository access
   - Check if the repository and tag exist
   - Ensure network connectivity to GitHub

3. **HAProxy Connection Issues:**
   - Verify HAProxy URL and credentials
   - Check network connectivity to HAProxy instance
   - Ensure HAProxy API is enabled and accessible

### Debug Mode

Enable debug logging:
```bash
juju model-config logging-config="<root>=DEBUG"
```

## Additional Resources

- [Contributing Guidelines](CONTRIBUTING.md) - How to contribute to this project
- [Juju SDK Documentation](https://juju.is/docs/sdk) - Official Juju development guide
- [Charmcraft Documentation](https://canonical-charmcraft.readthedocs-hosted.com/) - Charm building and packaging

## License

This project is licensed under the Apache License 2.0. See the [LICENSE](LICENSE) file for details.
