# TAPL Language Support Extension

This folder contains the TAPL Language Support Extension.

## Features

Basic language support consisting of the following:

- syntax highlighting
- basic indentation handling on enter
- recognition of TAPL's .tim files

## Requirements

Local development/usage:\
Run `TAPL Language Support` from the Run and Debug menu.

## Extension Settings

Currently there are no extension settings exposed.

## Known Issues

No known issues yet.

## Building and Deploying Extension

```bash
# enter the directory
cd tools/vscode/tapl-lang

# package the extension
vsce package
# tapl-lang-x.y.z.vsix generated

# publish the extension
vsce publish
# tapl-lang.tapl-lang published to VS Code Marketplace
```

## Release Notes

Release notes and changelog can be found [here](/tools/vscode/tapl-lang/CHANGELOG.md).
