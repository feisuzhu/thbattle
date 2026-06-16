use std::fmt::Debug;
use std::marker::Unsize;
use std::mem::MaybeUninit;
use std::ops::{Deref, DerefMut};
use std::ptr;
use std::ptr::{DynMetadata, Pointee};

pub trait TraitObject = Pointee<Metadata = DynMetadata<Self>>;

/// Zero-sized trait object wrapper — stores only a vtable.
/// Useful for function dispatch when the concrete type carries no data.
///
/// `Copy` + `Clone`.
pub struct ZeroSized<T: ?Sized + TraitObject> {
    metadata: DynMetadata<T>,
}

impl<T: ?Sized + TraitObject> Copy for ZeroSized<T> {}

impl<T: ?Sized + TraitObject> Clone for ZeroSized<T> {
    fn clone(&self) -> Self {
        *self
    }
}

impl<T: ?Sized + TraitObject> Deref for ZeroSized<T> {
    type Target = T;

    fn deref(&self) -> &Self::Target {
        let thin = ptr::without_provenance::<()>(self.metadata.align_of());
        // SAFETY: size is 0 (asserted at new()), dangling ptr is fine.
        unsafe { &*ptr::from_raw_parts(thin, self.metadata) }
    }
}

impl<T: ?Sized + TraitObject> DerefMut for ZeroSized<T> {
    fn deref_mut(&mut self) -> &mut Self::Target {
        let thin = ptr::without_provenance_mut::<()>(self.metadata.align_of());
        unsafe { &mut *ptr::from_raw_parts_mut(thin, self.metadata) }
    }
}

impl<T: ?Sized + TraitObject> ZeroSized<T> {
    pub fn new<U: Debug + Copy + Unsize<T> + 'static>(val: U) -> Self {
        const {
            assert!(size_of::<U>() == 0, "ZeroSized requires a zero-sized type");
        }
        Self {
            metadata: ptr::metadata(&raw const val as *const T),
        }
    }
}

// ---------------------------------------------------------------------------
/// Inline storage for a DST (dynamically-sized type).
///
/// `N` is the byte capacity of the inline buffer. `N` must be > 0 (use
/// [`ZeroSized`] for zero-sized types).
pub struct Embedded<T: ?Sized + TraitObject, const N: usize> {
    buf: [MaybeUninit<u8>; N],
    metadata: DynMetadata<T>,
}

impl<T: ?Sized + TraitObject, const N: usize> Drop for Embedded<T, N> {
    fn drop(&mut self) {
        // SAFETY: vtable obtained from the concrete type at construction.
        // The buffer holds a valid instance of the concrete type.
        unsafe {
            let fat: *mut T =
                ptr::from_raw_parts_mut(self.buf.as_mut_ptr() as *mut (), self.metadata);
            ptr::drop_in_place(fat);
        }
    }
}

impl<T: ?Sized + TraitObject, const N: usize> Deref for Embedded<T, N> {
    type Target = T;

    fn deref(&self) -> &Self::Target {
        // SAFETY: buffer holds a valid instance.
        unsafe {
            &*ptr::from_raw_parts(
                self.buf.as_ptr() as *const (),
                self.metadata,
            )
        }
    }
}

impl<T: ?Sized + TraitObject, const N: usize> DerefMut for Embedded<T, N> {
    fn deref_mut(&mut self) -> &mut Self::Target {
        unsafe {
            &mut *ptr::from_raw_parts_mut(
                self.buf.as_mut_ptr() as *mut (),
                self.metadata,
            )
        }
    }
}

impl<T: ?Sized + TraitObject, const N: usize> Embedded<T, N> {
    /// Construct an `Embedded` from a concrete type.
    ///
    /// The value must fit within `N` bytes and have alignment ≤
    /// `align_of::<usize>()` (struct alignment is pinned by `DynMetadata`).
    ///
    /// # Panics
    /// Compile-time panic if `N == 0` — use [`ZeroSized`] instead.
    pub fn new<U: Debug + Unsize<T> + 'static>(val: U) -> Self {
        const {
            assert!(N > 0, "Embedded requires N > 0; use ZeroSized for zero-sized types");
            assert!(size_of::<U>() <= N, "Value too large for Embedded buffer");
            assert!(
                align_of::<U>() <= align_of::<usize>(),
                "Value alignment exceeds Embedded buffer alignment"
            );
        }

        // Obtain vtable via unsizing coercion before the value is moved.
        let metadata = ptr::metadata(&raw const val as *const T);

        let mut this = Embedded {
            buf: [MaybeUninit::uninit(); N],
            metadata,
        };

        // SAFETY: size and alignment checked at compile time above.
        // ptr::read copies the bits; forget prevents double-drop.
        unsafe {
            ptr::write(this.buf.as_mut_ptr() as *mut U, ptr::read(&val));
        }
        core::mem::forget(val);

        this
    }
}

/// Extension trait providing `get_disjoint_mut` for any slice.
///
/// Replaces `stack_dst::SliceDst` which we remove together with `stack_dst`.
pub trait SliceExt {
    type Item;

    /// Returns mutable references to `M` distinct elements.
    fn get_disjoint_mut<const M: usize>(
        &mut self,
        indices: [usize; M],
    ) -> Result<[&mut Self::Item; M], &'static str>;
}

impl<T> SliceExt for [T] {
    type Item = T;

    fn get_disjoint_mut<const M: usize>(
        &mut self,
        indices: [usize; M],
    ) -> Result<[&mut T; M], &'static str> {
        let len = self.len();

        for &i in &indices {
            if i >= len {
                return Err("index out of bounds");
            }
        }

        for i in 0..M {
            for j in (i + 1)..M {
                if indices[i] == indices[j] {
                    return Err("duplicate indices");
                }
            }
        }

        // SAFETY: all indices are in bounds and pairwise distinct.
        unsafe {
            let ptr = self.as_mut_ptr();
            Ok(std::array::from_fn(|i| &mut *ptr.add(indices[i])))
        }
    }
}
