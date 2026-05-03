import argparse
import json
from pathlib import Path


def build_script(product: dict) -> str:
    highlights = " ".join([f"- {h}" for h in product.get("highlights", [])])
    return (
        f"วันนี้มารีวิว {product['name']} ราคา {product['price']} บาท "
        f"จุดเด่นคือ {highlights} "
        f"ถ้าสนใจ {product.get('cta', 'กดดูรายละเอียดสินค้าได้เลย')}"
    )


def mock_render_video(product: dict, script: str, out_video: Path):
    # Prototype placeholder: in production use moviepy + TTS + assets
    out_video.write_text(
        f"PROTOTYPE VIDEO FILE FOR {product['id']}\nSCRIPT:\n{script}\n",
        encoding="utf-8",
    )


def save_metadata(product: dict, out_meta: Path):
    payload = {
        "title": f"รีวิว {product['name']}",
        "description": "#รีวิวสินค้า #shopee #ของดีบอกต่อ",
        "related_product_ids": [product["id"]],
        "human_review_required": True,
    }
    out_meta.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)
    videos_dir = output_path / "videos"
    meta_dir = output_path / "metadata"
    videos_dir.mkdir(parents=True, exist_ok=True)
    meta_dir.mkdir(parents=True, exist_ok=True)

    products = json.loads(input_path.read_text(encoding="utf-8"))
    for product in products:
        script = build_script(product)
        mock_render_video(product, script, videos_dir / f"{product['id']}.mp4")
        save_metadata(product, meta_dir / f"{product['id']}.json")

    print(f"Done: generated {len(products)} items -> {output_path}")


if __name__ == "__main__":
    main()
