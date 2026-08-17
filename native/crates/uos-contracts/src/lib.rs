#![no_std]
#![forbid(unsafe_code)]

//! Native, allocation-free UniversalOS compatibility contracts.
//!
//! This is the first Rust migration target for the Python reference model. It
//! intentionally contains no parser, network, USB, bootloader, filesystem, or
//! hardware-driver code. Those layers must supply validated facts and signed
//! catalog data before these contracts select a Bootstrap Capsule.

#[derive(Clone, Copy, Debug, Eq, PartialEq, Ord, PartialOrd)]
pub struct Version {
    pub major: u16,
    pub minor: u16,
    pub patch: u16,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum Architecture {
    Arm64,
    Armv7,
    X86_64,
    Riscv64,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum PartitionModel {
    Ab,
    Transactional,
    SingleSlot,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum Transport {
    Fastboot,
    Recovery,
    Adb,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct DiscoveryFacts<'a> {
    pub architecture: Architecture,
    pub board_family: &'a str,
    pub soc_family: &'a str,
    pub partition_model: PartitionModel,
    pub transport: Transport,
    pub bootloader_unlocked: bool,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct BootstrapCapsule<'a> {
    pub id: &'a str,
    pub version: Version,
    pub architecture: Architecture,
    pub board_family: &'a str,
    pub soc_family: &'a str,
    pub partition_model: PartitionModel,
    pub transport: Transport,
    pub offline_recovery: bool,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum SelectionError {
    LockedBootloader,
    NoCompatibleCapsule,
    AmbiguousNewestCapsule,
}

fn capsule_matches(facts: &DiscoveryFacts<'_>, capsule: &BootstrapCapsule<'_>) -> bool {
    facts.architecture == capsule.architecture
        && facts.board_family == capsule.board_family
        && facts.soc_family == capsule.soc_family
        && facts.partition_model == capsule.partition_model
        && facts.transport == capsule.transport
        && capsule.offline_recovery
}

/// Select the unique newest exact Bootstrap Capsule from already verified data.
///
/// Signatures and catalog expiry are intentionally checked outside this small
/// `no_std` crate. The caller must never pass server-selected unverified data.
pub fn select_bootstrap<'a, 'b>(
    facts: &DiscoveryFacts<'_>,
    capsules: &'a [BootstrapCapsule<'b>],
) -> Result<&'a BootstrapCapsule<'b>, SelectionError> {
    if !facts.bootloader_unlocked {
        return Err(SelectionError::LockedBootloader);
    }

    let mut selected: Option<&BootstrapCapsule<'b>> = None;
    for capsule in capsules {
        if !capsule_matches(facts, capsule) {
            continue;
        }
        match selected {
            None => selected = Some(capsule),
            Some(current) if capsule.version > current.version => selected = Some(capsule),
            Some(current) if capsule.version == current.version => {
                return Err(SelectionError::AmbiguousNewestCapsule);
            }
            Some(_) => {}
        }
    }
    selected.ok_or(SelectionError::NoCompatibleCapsule)
}

#[cfg(test)]
mod tests {
    use super::*;

    const FACTS: DiscoveryFacts<'static> = DiscoveryFacts {
        architecture: Architecture::Arm64,
        board_family: "synthetic-orion",
        soc_family: "synthetic-q1",
        partition_model: PartitionModel::Ab,
        transport: Transport::Fastboot,
        bootloader_unlocked: true,
    };

    const fn capsule(id: &'static str, version: Version) -> BootstrapCapsule<'static> {
        BootstrapCapsule {
            id,
            version,
            architecture: Architecture::Arm64,
            board_family: "synthetic-orion",
            soc_family: "synthetic-q1",
            partition_model: PartitionModel::Ab,
            transport: Transport::Fastboot,
            offline_recovery: true,
        }
    }

    #[test]
    fn selects_newest_exact_capsule() {
        let old = capsule("uos.bootstrap.orion", Version { major: 0, minor: 1, patch: 0 });
        let new = capsule("uos.bootstrap.orion", Version { major: 0, minor: 1, patch: 1 });
        assert_eq!(select_bootstrap(&FACTS, &[old, new]).unwrap().version, new.version);
    }

    #[test]
    fn rejects_locked_or_ambiguous_bootstrap() {
        let capsule = capsule("uos.bootstrap.orion", Version { major: 0, minor: 1, patch: 0 });
        let locked = DiscoveryFacts { bootloader_unlocked: false, ..FACTS };
        assert_eq!(select_bootstrap(&locked, &[capsule]), Err(SelectionError::LockedBootloader));
        let second = BootstrapCapsule { id: "uos.bootstrap.orion-alt", ..capsule };
        assert_eq!(select_bootstrap(&FACTS, &[capsule, second]), Err(SelectionError::AmbiguousNewestCapsule));
    }
}
