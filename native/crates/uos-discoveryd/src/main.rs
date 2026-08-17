#![forbid(unsafe_code)]

//! Host/QEMU-facing Discovery Base service scaffold.
//!
//! This executable is intentionally a deterministic smoke-test utility until a
//! native IPC/service manager and real local hardware-fact source are available.

use uos_contracts::{
    select_bootstrap, Architecture, BootstrapCapsule, DiscoveryFacts, PartitionModel, Transport,
    Version,
};

fn main() {
    let facts = DiscoveryFacts {
        architecture: Architecture::Arm64,
        board_family: "synthetic-orion",
        soc_family: "synthetic-q1",
        partition_model: PartitionModel::Ab,
        transport: Transport::Fastboot,
        bootloader_unlocked: true,
    };
    let capsules = [BootstrapCapsule {
        id: "uos.bootstrap.synthetic-orion",
        version: Version { major: 0, minor: 1, patch: 0 },
        architecture: Architecture::Arm64,
        board_family: "synthetic-orion",
        soc_family: "synthetic-q1",
        partition_model: PartitionModel::Ab,
        transport: Transport::Fastboot,
        offline_recovery: true,
    }];

    match select_bootstrap(&facts, &capsules) {
        Ok(capsule) => println!("UniversalOS Discovery Base selected {} {}.{}.{}", capsule.id, capsule.version.major, capsule.version.minor, capsule.version.patch),
        Err(error) => eprintln!("UniversalOS Discovery Base selection failed: {error:?}"),
    }
}
