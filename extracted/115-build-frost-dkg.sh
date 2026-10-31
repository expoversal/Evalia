# Build the ceremony tool from source, verify the hash, pin it
git clone --depth 1 --branch v2.0.0 https://github.com/ZcashFoundation/frost.git
cd frost/frost-dkg
cargo build --release
# Hash the built binary
sha256sum target/release/frost-dkg
# Publish the hash in the ceremony checklist and on the tender portal
