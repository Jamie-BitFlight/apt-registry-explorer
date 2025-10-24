"""
APT sources file builder with GPG/arch/signed-by options.
"""

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class SourceOptions:
    """Options for apt.sources configuration."""

    signed_by: Optional[str] = None
    architectures: Optional[List[str]] = None
    languages: Optional[List[str]] = None
    targets: Optional[List[str]] = None
    trusted: bool = False


class SourcesBuilder:
    """Build apt.sources configuration from repository information."""

    def __init__(self):
        """Initialize sources builder."""
        self.entries = []

    def add_source(
        self,
        source_type: str,
        url: str,
        suite: str,
        components: List[str],
        options: Optional[SourceOptions] = None,
    ):
        """
        Add a source entry.

        Args:
            source_type: Type of source ('deb' or 'deb-src')
            url: Repository URL
            suite: Distribution suite/release
            components: List of components (main, contrib, etc.)
            options: Optional source options
        """
        entry = {
            "type": source_type,
            "url": url,
            "suite": suite,
            "components": components,
            "options": options or SourceOptions(),
        }
        self.entries.append(entry)

    def build_deb822(self) -> str:
        """
        Build deb822 format sources file.

        Returns:
            String content for .sources file
        """
        output = []
        
        for entry in self.entries:
            lines = []
            
            # Add Types field
            lines.append(f"Types: {entry['type']}")
            
            # Add URIs field
            lines.append(f"URIs: {entry['url']}")
            
            # Add Suites field
            lines.append(f"Suites: {entry['suite']}")
            
            # Add Components field
            components_str = " ".join(entry['components'])
            lines.append(f"Components: {components_str}")
            
            # Add options
            opts = entry['options']
            if opts.signed_by:
                lines.append(f"Signed-By: {opts.signed_by}")
            
            if opts.architectures:
                arch_str = " ".join(opts.architectures)
                lines.append(f"Architectures: {arch_str}")
            
            if opts.languages:
                lang_str = " ".join(opts.languages)
                lines.append(f"Languages: {lang_str}")
            
            if opts.targets:
                targets_str = " ".join(opts.targets)
                lines.append(f"Targets: {targets_str}")
            
            if opts.trusted:
                lines.append("Trusted: yes")
            
            output.append("\n".join(lines))
        
        return "\n\n".join(output)

    def build_one_line(self) -> List[str]:
        """
        Build traditional one-line format sources.

        Returns:
            List of source lines
        """
        output = []
        
        for entry in self.entries:
            opts = entry['options']
            options_parts = []
            
            if opts.signed_by:
                options_parts.append(f"signed-by={opts.signed_by}")
            
            if opts.architectures:
                arch_str = ",".join(opts.architectures)
                options_parts.append(f"arch={arch_str}")
            
            if opts.trusted:
                options_parts.append("trusted=yes")
            
            # Build the line
            parts = [entry['type']]
            
            if options_parts:
                options_str = " ".join(options_parts)
                parts.append(f"[{options_str}]")
            
            parts.append(entry['url'])
            parts.append(entry['suite'])
            parts.extend(entry['components'])
            
            output.append(" ".join(parts))
        
        return output

    def parse_deb_line(self, line: str) -> dict:
        """
        Parse a traditional one-line deb source line.

        Args:
            line: Source line to parse

        Returns:
            Dictionary with parsed components
        """
        line = line.strip()
        
        # Skip comments and empty lines
        if not line or line.startswith("#"):
            return None
        
        # Parse options block if present (enclosed in [])
        options = SourceOptions()
        options_match = None
        import re
        options_pattern = r'\[([^\]]+)\]'
        match = re.search(options_pattern, line)
        
        if match:
            options_str = match.group(1)
            # Remove the options block from the line
            line = re.sub(options_pattern, '', line).strip()
            
            # Parse individual options
            for opt in options_str.split():
                if "=" in opt:
                    key, value = opt.split("=", 1)
                    if key == "signed-by":
                        options.signed_by = value
                    elif key == "arch":
                        options.architectures = value.split(",")
                    elif key == "trusted" and value.lower() == "yes":
                        options.trusted = True
        
        # Now parse the remaining parts
        parts = line.split()
        if len(parts) < 4:
            return None
        
        source_type = parts[0]
        url = parts[1]
        suite = parts[2]
        components = parts[3:]
        
        return {
            "type": source_type,
            "url": url,
            "suite": suite,
            "components": components,
            "options": options,
        }
