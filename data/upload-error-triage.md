# "Too large" — which number is the form actually checking

Five different messages, one sentence in common: something is over a limit, and the page does not say what. The unit printed in the message, or the transport the page uses, decides which fix works. Applying the wrong one either wastes pixels or leaves the file rejected.

| Message | The number that is over the limit | How to tell | The fix that works |
|---|---|---|---|
| `file too large` (MB / KB in the message) | Bytes on disk | Compare `size` with the stated limit, in the same unit base | Re-encode to a byte target below the limit |
| `image too large to upload` | Bytes **or** pixel width/height | Check the bytes first; if the bytes are already under the limit and it still fails, it is a dimension limit | Re-encode for bytes, resize for pixels — compressing harder never moves a pixel cap |
| `image size too large` | Decoded area, not disk size | Compute `width × height`; a small file can be a huge image | Downscale. A byte target only removes pixels it has to |
| `the file you are trying to upload is too large` | Whichever unit the message prints | MB/KB → bytes; px / MP / dimensions → area | Re-encode for bytes, resize for area |
| Any of the above, but the page posts JSON | The request body, not the file | Open devtools → Network → the request that fails; `application/json` means base64 | Compress to the body budget, not the file budget |

## The coefficients, measured

**Base64 transport.** A file posted as base64 inside JSON grows by 4/3, and the JSON wrapper adds bytes on top. On the page measured, the wrapper cost 85 bytes. A 10 MB limit therefore accepted a 7,499,934-byte file — setting 9,765 KB (the multipart answer) would have been rejected by the body size, and setting 7,324 KB costs quality for nothing when the page uses multipart. Multipart overhead on the same page measured 183 to 198 bytes, which is why 9,765 KB is enough there.
Source: https://crunchimage.com/file-too-large-to-upload

**KB against MB.** A compressor that reads "KB" as 1,024 bytes and a form that reads "MB" as 1,000,000 bytes disagree by 4.8576% at that prefix step (1024² / 10⁶ = 1.048576). Measured: typing 2000 KB produced a 2,014,942-byte file, which a 2,000,000-byte limit rejects by 14,942 bytes; 1953 KB produced 1,990,266 bytes and passed with 9,734 bytes to spare. The round number is the one that fails.
Source: https://crunchimage.com/file-too-large

**Bytes against area.** An 84,394-byte PNG measuring 4000 × 4000 is 16.00 megapixels, which decodes to 64,000,000 bytes of pixels — 758 times its size on disk. Across twelve real files the factor between bytes on disk and bytes of pixels ran from 6.05× to 835×. So "image size" is two numbers, and the message never says which.
Source: https://crunchimage.com/image-size-too-large

**Why compressing does not fix a pixel cap.** A 54-megapixel photograph (6000 × 9000, 11,525,365 bytes) compressed to a 2 MB target came back at 5755 × 8633 — 49.68 megapixels, 8% fewer pixels than the original, for an 82% cut in bytes. A form that caps width at 2000 pixels rejects that file at 2 MB, at 1 MB and at 5 MB alike.
Source: https://crunchimage.com/image-too-large-to-upload

## Reading the message in ten seconds

1. Look for a unit: `MB` or `KB` means bytes; `px`, `MP`, `pixels`, `dimensions` means area.
2. If there is no unit, check the file: if it is under the byte limit and still rejected, it is a dimension or format limit.
3. Check the transport: a JSON request body is bigger than the file, and the gap is not a rounding error.

The arithmetic for steps 1 and 3 is in `tools/byte_budget.py`; the tables it refers to are in `data/`.
