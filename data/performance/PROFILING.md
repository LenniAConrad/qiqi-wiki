<!-- SPDX-License-Identifier: GPL-3.0-only -->
# Reproducing the component analysis

Run from the sibling Voxelgame checkout. Complete native instructions are in
`docs/DEBUGGING.md` there. Use disposable offscreen sessions and a fixture save.

```sh
cargo build --release --features devtools
VOXELGAME_PROFILE_JSON=/tmp/profile.json \
VOXELGAME_SAVE_PATH=/absolute/path/to/disposable-fixture.vxw \
  target/release/voxelgame --headless --bench=8 --bench-warmup=20 \
  --window=960x540 --view-distance=32 --shader=fast --weather=clear --time=0.43
```

Match the original fixture, camera and look direction for comparisons; see
`fixtures.csv` and the original replay scenarios. A debug step accepts
`{"command":"step","frames":120,"render":true,"profile":true}` and normal
held keys such as `W` and `ControlLeft` for movement. Warm up before measuring a
settled scene. Set `VOXELGAME_PROFILE_HIDE_TREES=1` in a fresh disposable process
for the geometry comparison; this retains world occupancy and collision.

Only exclusive CPU values add without double counting; worker wall durations
overlap. Process CPU time includes all threads. Scopes crossing a measurement
boundary are omitted. GPU pass timestamps exclude uploads and queue waits.
CPU and GPU values must not be added or converted directly into windowed FPS.
Normal builds compile out profiling hooks. No sampling flame graph was taken.

