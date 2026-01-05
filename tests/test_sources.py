"""
Tests for sources module.
"""

from apt_registry_explorer.sources import SourceOptions, SourcesBuilder


def test_sources_builder_add_source():
    """Test adding a source to builder."""
    builder = SourcesBuilder()
    builder.add_source("deb", "https://example.com/debian", "stable", ["main", "contrib"])

    assert len(builder.entries) == 1
    assert builder.entries[0]["type"] == "deb"
    assert builder.entries[0]["url"] == "https://example.com/debian"


def test_build_deb822():
    """Test building deb822 format."""
    builder = SourcesBuilder()
    options = SourceOptions(architectures=["amd64"], signed_by="/usr/share/keyrings/example.gpg")
    builder.add_source("deb", "https://example.com/debian", "stable", ["main"], options)

    output = builder.build_deb822()
    assert "Types: deb" in output
    assert "URIs: https://example.com/debian" in output
    assert "Suites: stable" in output
    assert "Components: main" in output
    assert "Signed-By: /usr/share/keyrings/example.gpg" in output
    assert "Architectures: amd64" in output


def test_build_one_line():
    """Test building one-line format."""
    builder = SourcesBuilder()
    options = SourceOptions(architectures=["amd64"])
    builder.add_source("deb", "https://example.com/debian", "stable", ["main", "contrib"], options)

    lines = builder.build_one_line()
    assert len(lines) == 1
    assert lines[0].startswith("deb")
    assert "arch=amd64" in lines[0]
    assert "https://example.com/debian" in lines[0]
    assert "stable" in lines[0]
    assert "main" in lines[0]
    assert "contrib" in lines[0]


def test_parse_deb_line():
    """Test parsing a deb line."""
    builder = SourcesBuilder()
    line = "deb [arch=amd64 signed-by=/usr/share/keyrings/test.gpg] https://example.com/debian stable main contrib"

    parsed = builder.parse_deb_line(line)

    assert parsed is not None
    assert parsed["type"] == "deb"
    assert parsed["url"] == "https://example.com/debian"
    assert parsed["suite"] == "stable"
    assert parsed["components"] == ["main", "contrib"]
    assert parsed["options"].architectures == ["amd64"]
    assert parsed["options"].signed_by == "/usr/share/keyrings/test.gpg"


def test_parse_simple_deb_line():
    """Test parsing a simple deb line without options."""
    builder = SourcesBuilder()
    line = "deb https://example.com/debian stable main"

    parsed = builder.parse_deb_line(line)

    assert parsed is not None
    assert parsed["type"] == "deb"
    assert parsed["url"] == "https://example.com/debian"
    assert parsed["suite"] == "stable"
    assert parsed["components"] == ["main"]
