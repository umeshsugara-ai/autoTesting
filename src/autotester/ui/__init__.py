"""The web UI. A thin viewer/editor over project files — never a second store
(design principle 8): every route reads and writes through the same
`ProjectStore`/`SecretStore`/stages the CLI uses."""
