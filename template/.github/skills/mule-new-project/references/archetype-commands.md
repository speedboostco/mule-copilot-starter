# Archetype commands (fill placeholders from profile.md)

Install or refresh the local archetype only when `~/.m2` lacks the version or the archetype changed:
```bash
cd <workspace>/<archetype-dir>
mvn clean install
```

Generate from the workspace root, non-interactive. Read the archetype's `archetype-metadata.xml` for the real required properties; the list below is the common shape:
```bash
cd <workspace>
mvn archetype:generate \
  -DarchetypeGroupId=<archetype groupId> \
  -DarchetypeArtifactId=<archetype artifactId> \
  -DarchetypeVersion=<archetype version> \
  -DgroupId=<workspace groupId> \
  -DartifactId=<prefix>-<name>-<layer> \
  -Dversion=1.0.0-SNAPSHOT \
  -DpomParentVersion=<newest parent used by same-layer projects> \
  -DvisualizerLayer=<Experience|Process|System> \
  -DspecName=<name>-<layer> \
  -DspecVersion=1.0.0 \
  -D<other required properties>=<value> \
  -DinteractiveMode=false
```

Name rules:
- User gives `<prefix>-foo-sapi` → artifactId as given, specName without the prefix.
- User gives `foo-sapi` → add the workspace project prefix from `profile.md`.
- Layer suffix must match the workspace layer suffixes.
- App/error codes used for support or error reporting: ask if the value matters.
