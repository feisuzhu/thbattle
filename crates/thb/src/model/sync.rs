use erased_serde::{Deserializer, Serializer};
use serde::de::DeserializeOwned;
use serde::Serialize;

/// State that can be synchronized from the authoritative (server) side to a
/// replica (client) side.
///
/// The wire format is intentionally not fixed: the caller chooses any `serde`
/// data format (e.g. MessagePack or JSON) by constructing a concrete
/// serializer/deserializer and type-erasing it through [`erased_serde`].
/// Because the methods take erased trait objects instead of generic
/// `S: Serializer` parameters, this trait stays object-safe and can be used as
/// `dyn Synchronizable`.
///
/// ```ignore
/// // server: encode with whichever format you like
/// let mut buf = Vec::new();
/// let mut ser = rmp_serde::Serializer::new(&mut buf);
/// obj.dump(&mut <dyn erased_serde::Serializer>::erase(&mut ser))?;
///
/// // client: decode the same bytes back in place
/// let mut de = rmp_serde::Deserializer::new(&buf[..]);
/// obj.load(&mut <dyn erased_serde::Deserializer>::erase(&mut de))?;
/// ```
pub trait Synchronizable {
    /// Authoritative side: encode the current state into `serializer`.
    fn dump(&self, serializer: &mut dyn Serializer) -> Result<(), erased_serde::Error>;

    /// Replica side: overwrite the current state from `deserializer`.
    fn load<'de>(
        &mut self,
        deserializer: &mut dyn Deserializer<'de>,
    ) -> Result<(), erased_serde::Error>;
}

/// Thin newtype that makes any `Serialize + DeserializeOwned` value
/// [`Synchronizable`].
///
/// The newtype sidesteps the coherence problems of a blanket
/// `impl<T> Synchronizable for T`, while still working for arbitrary
/// serializable primitives.
pub struct SyncPrimitive<T>(pub T);

impl<T> Synchronizable for SyncPrimitive<T>
where
    T: Serialize + DeserializeOwned,
{
    fn dump(&self, ser: &mut dyn Serializer) -> Result<(), erased_serde::Error> {
        erased_serde::Serialize::erased_serialize(&self.0, ser)
    }

    fn load<'de>(&mut self, de: &mut dyn Deserializer<'de>) -> Result<(), erased_serde::Error> {
        self.0 = erased_serde::deserialize(de)?;
        Ok(())
    }
}
