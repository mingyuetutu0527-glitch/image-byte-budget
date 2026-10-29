# image-byte-budget

Measured output sizes from a browser-based "compress to an exact file size" tool, released as CSV so the numbers can be checked, reused, or argued with.

Most compression advice is written as if a byte target were a quality setting. It is not. Below a certain budget the encoder stops lowering quality and starts deleting pixels, so "100 KB" means a different picture depending on what the photo contains. These tables record what actually came back, run by run, with the source file named on every row.

## What is inside

| File | What it holds |
|---|---|
| `data/size-tier-ceilings.csv` | Nine byte tiers from 20 KB to 5 MB: what each one returned in pixels, bytes and quality, and which source file it was measured on |
| `data/jpg-vs-webp-same-budget.csv` | Six byte targets, one 24-megapixel photograph, JPG against WebP at the same ceiling |
| `data/file-types-at-100kb.csv` | Seven different kinds of picture (scan, text page, flat graphic, cut-out, gradient, product shot, small photo) all pushed to 100 KB |
| `data/quality-matched-encoding.csv` | The same seven files encoded at fixed q0.90 and q0.75 in both formats, so the "WebP is 25–34% smaller" claim can be compared at equal quality rather than equal size |
| `data/alpha-channel.csv` | One transparent cut-out through both encoders: what happened to the pixels that were fully transparent |
| `data/upload-error-triage.md` | The five different "too large" messages forms produce, which number each one is actually about, and the measured coefficients behind them |
| `tools/byte_budget.py` | Arithmetic only: KB/MB prefix conventions, base64 and multipart request overhead, and the largest file a given form limit really accepts |

## How the numbers were produced

- One browser session, Chrome 155.0.8059.85 on Windows 11, the compressor served from a local copy on 127.0.0.1 so no file left the machine.
- One file per run, through the normal file input. No batch, no server-side queue.
- Output bytes were read twice per row: once from the page's own result object, once by fetching the produced blob and reading `arrayBuffer().byteLength`. The two agreed on every row.
- Output dimensions were read by decoding the produced data URL back into an `Image` and taking `naturalWidth` / `naturalHeight`, not from the numbers the tool printed.
- "Quality" is the encoder setting the tool's own size search settled on, as a percentage.
- Elapsed times are the tool's own `Done in N ms` value and vary between runs on the same machine; they are included where the page reported them, and should be treated as ratios rather than absolutes.

The measurements were produced by the compressor at **https://crunchimage.com** — the same runs the site's pages describe. They are published here as data so that anyone can check a figure, quote it, or test it against their own encoder.

## What these numbers do not tell you

- They are not a model. Nothing here is interpolated: if a tier is missing, it was not measured.
- They come from one machine, one browser build and one encoder implementation. A different encoder's size search can land on a different step, which is why the same target produces lumpy jumps between tiers.
- Empty cells mean the page did not state that value, not that it was zero.
- A byte target is a ceiling, not a promise about quality. Two files with the same target and the same output size can look very different.

## License

Code (`tools/`) is MIT. Data (`data/`) is CC BY 4.0 — see `DATA-LICENSE.md`.
