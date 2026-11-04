"""Offline regression contracts for the public organisation profile README.

These checks intentionally validate Markdown structure and public-facing link
policy, not live third-party counters or anonymous playback permissions.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path
from urllib.parse import parse_qs, urlparse


ROOT = Path(__file__).resolve().parents[1]
PROFILE = ROOT / "profile" / "README.md"
ORG = "https://github.com/Shards-foundation"
FOLLOWERS = "https://github.com/orgs/Shards-foundation/followers"
PACKAGE = "https://pypi.org/project/shards-kernel/"

FEATURED_REPOS = (
    "Shards-kernel",
    "shards-agent-core",
    "Shards-Swarm-Agent",
    "Shards-Super-Intelligence-Agent",
    "AgentMesh",
    "omni-llm-orchestrator",
    "Shards-Rag",
    "shards-workflow-hub",
    "shards-playbooks",
    "Shards-Revenue-Engine",
    "Shards-Agent-Trading-Network",
    "PATENT-OS",
    "Components-library",
    "Lumina",
    "ai-agent-sketchbook",
)


def badge_link(markdown: str, label: str) -> tuple[str, str]:
    """Find one clickable image badge and return (image_src, link_target)."""
    pattern = (
        r"\[!\[" + re.escape(label) + r"\]\((https://[^)\s]+)\)\]"
        r"\((https://[^)\s]+)\)"
    )
    matches = re.findall(pattern, markdown)
    if len(matches) != 1:
        raise AssertionError(f"Expected exactly one clickable {label!r} badge; got {len(matches)}")
    return matches[0]


def showcase_section(markdown: str) -> str:
    match = re.search(
        r"(?ms)^## Shards in motion\s*$(.*?)^(?=## |\Z)",
        markdown,
    )
    if not match:
        raise AssertionError("The 'Shards in motion' section is missing")
    return match.group(1)


def check_showcase(markdown: str) -> str:
    """Validate EITHER private placeholder OR coherent public showcase links."""
    section = showcase_section(markdown)
    if re.search(r"publication pending", section, re.IGNORECASE):
        if not re.search(r"privat(?:e|ely)", section, re.IGNORECASE):
            raise AssertionError("Pending video needs an explicit private-access disclaimer")
        if not re.search(r"owner or explicitly authori[sz]ed viewers", section, re.IGNORECASE):
            raise AssertionError("Pending video must identify its authorised audience")
        if re.search(r"https?://|\]\(|<video\b|<iframe\b", section, re.IGNORECASE):
            raise AssertionError("Pending video must not expose a nonfunctional public CTA")
        return "private"

    # After publication both the clickable poster and the watch CTA must
    # use the SAME published video URL, not a private Google Drive file.
    poster = re.search(
        r"\[!\[(?:Watch|Play)[^\]]*\]\((https://[^)\s]+)\)\]"
        r"\((https://[^)\s]+)\)",
        section, re.IGNORECASE,
    )
    watch = re.search(r"(?<!!)\[(?:▶\s*)?Watch[^\]]+\]\((https://[^)\s]+)\)", section, re.IGNORECASE)
    if not poster or not watch:
        raise AssertionError("Public showcase must provide a linked image and a watch link")

    image_url, poster_target = poster.groups()
    watch_target = watch.group(1)
    if poster_target != watch_target:
        raise AssertionError("Poster link and watch link must target the same video")
    if not urlparse(image_url).netloc or not urlparse(watch_target).netloc:
        raise AssertionError("Public showcase URLs must have valid HTTPS hostnames")
    hostname = urlparse(watch_target).hostname
    if hostname == "drive.google.com" or (hostname and hostname.endswith(".drive.google.com")):
        raise AssertionError("Drive links need independent permission verification")
    return "public"


class ProfileReadmeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.readme = PROFILE.read_text(encoding="utf-8")

    def test_views_badge_is_clickable_and_configured_for_this_org(self) -> None:
        image, target = badge_link(self.readme, "Profile views")
        self.assertEqual(target, ORG)
        parsed = urlparse(image)
        self.assertEqual(parsed.netloc, "komarev.com")
        self.assertEqual(parsed.path, "/ghpvc/")
        self.assertEqual(parse_qs(parsed.query).get("username"), ["Shards-foundation"])
        self.assertEqual(parse_qs(parsed.query).get("style"), ["flat-square"])

    def test_followers_badge_links_to_org_followers_page(self) -> None:
        image, target = badge_link(self.readme, "GitHub followers")
        self.assertEqual(target, FOLLOWERS)
        parsed = urlparse(image)
        self.assertEqual(parsed.netloc, "img.shields.io")
        self.assertEqual(parsed.path, "/github/followers/Shards-foundation")
        self.assertEqual(parse_qs(parsed.query).get("label"), ["Followers"])

    def test_animated_logo_is_committed_and_uses_absolute_url(self) -> None:
        self.assertIn(
            'src="https://raw.githubusercontent.com/Shards-foundation/.github/'
            'main/profile/assets/shards-inc-animated.gif"',
            self.readme,
        )
        logo = ROOT / "profile" / "assets" / "shards-inc-animated.gif"
        self.assertTrue(logo.is_file(), "Animated logo must be committed")
        self.assertIn(logo.read_bytes()[:6], (b"GIF87a", b"GIF89a"))

    def test_showcase_access_policy_is_explicit(self) -> None:
        self.assertIn(check_showcase(self.readme), ("private", "public"))

    def test_private_video_never_has_broken_watch_link(self) -> None:
        if check_showcase(self.readme) == "private":
            section = showcase_section(self.readme)
            self.assertNotIn("drive.google.com", section)
            self.assertNotRegex(section, r"\[.*Watch.*\]\(")

    def test_published_showcase_requires_image_and_watch_link_same_target(self) -> None:
        public_fixture = (
            "## Shards in motion\n\n"
            "[![Watch Shards showcase](https://example.org/preview.gif)]"
            "(https://example.org/showcase.mp4)\n\n"
            "[▶ Watch the video](https://example.org/showcase.mp4)\n\n"
            "## What we're building\n"
        )
        self.assertEqual(check_showcase(public_fixture), "public")
        with self.assertRaisesRegex(AssertionError, "same video"):
            check_showcase(public_fixture.replace(
                "Watch the video](https://example.org/showcase.mp4)",
                "Watch the video](https://example.org/wrong.mp4)",
            ))

    def test_all_featured_repository_links_remain(self) -> None:
        for name in FEATURED_REPOS:
            with self.subTest(repo=name):
                self.assertIn(f"https://github.com/Shards-foundation/{name}", self.readme)

    def test_package_and_entrypoint_links_remain(self) -> None:
        for url in (
            PACKAGE,
            "https://github.com/Shards-foundation/Shards-kernel/actions/workflows/ci.yml",
            "https://github.com/Shards-foundation/Shards-kernel/blob/main/LICENSE",
            "https://github.com/Shards-foundation/Shards-kernel/blob/main/docs/AGENT_QUICKSTART.md",
        ):
            with self.subTest(url=url):
                self.assertIn(url, self.readme)
        self.assertIn("python -m pip install shards-kernel", self.readme)
        self.assertIn("shards-kernel demo --json", self.readme)


if __name__ == "__main__":
    unittest.main()
