use std::fmt::Debug;
use std::marker::Unsize;
use std::ops::{Deref, DerefMut};
use std::ptr;
use std::ptr::{DynMetadata, Pointee};

pub(crate) trait TraitObject = Pointee<Metadata = DynMetadata<Self>>;

///|
/// Encapsuled zero sized trait object. Just a vtable ptr, useful for function dispatch.
/// Solely for 'Copy', or we use stack_dst
pub struct ZeroSized<T: ?Sized + TraitObject> {
    vtable: DynMetadata<T>,
}

impl<T: ?Sized + TraitObject> Copy for ZeroSized<T> {}

impl<T: ?Sized + TraitObject> Clone for ZeroSized<T> {
    fn clone(&self) -> Self {
        Self {
            vtable: self.vtable,
        }
    }
}

impl<T: ?Sized + TraitObject> Deref for ZeroSized<T> {
    type Target = T;

    fn deref(&self) -> &Self::Target {
        let thin = std::ptr::without_provenance::<()>(self.vtable.align_of());
        // SAFETY: Size asserted at Self::new(), dangling ptr is OK
        unsafe { &*ptr::from_raw_parts(thin, self.vtable) }
    }
}

impl<T: ?Sized + TraitObject> DerefMut for ZeroSized<T> {
    fn deref_mut(&mut self) -> &mut Self::Target {
        let thin = std::ptr::without_provenance_mut::<()>(self.vtable.align_of());
        // SAFETY: Size asserted at Self::new(), dangling ptr is OK
        unsafe { &mut *(ptr::from_raw_parts_mut(thin, self.vtable)) }
    }
}

impl<T: ?Sized + TraitObject> ZeroSized<T> {
    pub fn new<U: Debug + Copy + Unsize<T> + 'static>(val: U) -> Self {
        const {
            assert!(size_of::<U>() == 0, "Requires a zero sized struct");
        };
        Self {
            vtable: ptr::metadata(&val as *const T),
        }
    }
}
