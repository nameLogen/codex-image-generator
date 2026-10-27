import asyncio
import base64
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from codex_image_generator import server


PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+aZI0AAAAASUVORK5CYII="
)


class GenerateImageTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.output = self.root / "generated" / "output.png"
        self.reference = self.root / "参考图.PNG"
        self.reference.write_bytes(PNG)

        config = patch.object(server, "get_proxy_config", return_value=("http://proxy/v1", "test-key"))
        config.start()
        self.addCleanup(config.stop)
        stream = patch.object(server.httpx, "stream")
        self.stream = stream.start()
        self.addCleanup(stream.stop)
        response = self.stream.return_value.__enter__.return_value
        response.iter_lines.return_value = [
            "data: " + json.dumps({
                "type": "response.output_item.done",
                "item": {
                    "type": "image_generation_call",
                    "result": base64.b64encode(PNG).decode("ascii"),
                    "revised_prompt": "revised",
                },
            }),
            "data: [DONE]",
        ]

    def test_text_only_remains_compatible(self):
        saved, revised = server.generate_image("海边灯塔", output_path=str(self.output))
        payload = self.stream.call_args.kwargs["json"]
        self.assertEqual(payload["input"], [{"role": "user", "content": "海边灯塔"}])
        self.assertEqual(Path(saved).read_bytes(), PNG)
        self.assertEqual(revised, "revised")

    def test_reference_images_are_embedded_in_order(self):
        other = self.root / "other.png"
        other.write_bytes(PNG + b"\x00")
        server.generate_image(
            "参考这两张图", output_path=str(self.output),
            reference_image_paths=[str(self.reference), str(other)],
        )
        content = self.stream.call_args.kwargs["json"]["input"][0]["content"]
        self.assertEqual(content[0], {"type": "input_text", "text": "参考这两张图"})
        self.assertEqual(len(content), 3)
        for item, path in zip(content[1:], [self.reference, other]):
            self.assertEqual(item["type"], "input_image")
            prefix, encoded = item["image_url"].split(",", 1)
            self.assertEqual(prefix, "data:image/png;base64")
            self.assertEqual(base64.b64decode(encoded), path.read_bytes())
        self.assertEqual(self.output.read_bytes(), PNG)

    def test_empty_list_uses_text_only(self):
        server.generate_image("test", output_path=str(self.output), reference_image_paths=[])
        self.assertEqual(self.stream.call_args.kwargs["json"]["input"][0]["content"], "test")

    def test_missing_reference_fails_before_request(self):
        with self.assertRaises(FileNotFoundError):
            server.generate_image("test", reference_image_paths=[str(self.root / "missing.png")])
        self.stream.assert_not_called()

    def test_invalid_references_fail_before_request(self):
        empty = self.root / "empty.png"
        empty.touch()
        for value in ["image.png", [""], [None], [str(self.root / "file.txt")], [str(empty)]]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                server.generate_image("test", reference_image_paths=value)
        self.stream.assert_not_called()

    def test_mcp_schema_exposes_reference_images(self):
        tool = asyncio.run(server.list_tools())[0]
        self.assertEqual(tool.inputSchema["properties"]["reference_image_paths"]["type"], "array")
        self.assertEqual(tool.inputSchema["required"], ["prompt"])

    def test_mcp_forwards_reference_images(self):
        references = [str(self.reference)]
        with patch.object(server, "generate_image", return_value=(str(self.output), "")) as generate:
            result = asyncio.run(server.call_tool("generate_image", {
                "prompt": "test", "reference_image_paths": references,
            }))
        generate.assert_called_once_with("test", "1024x1024", "output.png", reference_image_paths=references)
        self.assertIn(str(self.output), result[0].text)


if __name__ == "__main__":
    unittest.main()
