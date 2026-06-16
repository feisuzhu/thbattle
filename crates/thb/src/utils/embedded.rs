use std::fmt::Debug;
use std::marker::Unsize;
use std::mem::MaybeUninit;
use std::ops::{Deref, DerefMut};
use std::ptr;
use std::ptr::{DynMetadata, Pointee};

pub trait TraitObject = Pointee<Metadata = DynMetadata<Self>>;

/// Inline storage for a DST (dynamically-sized type).
///
/// `N` is the byte size of the inline data buffer.
/// - `N == 0` (previously `ZeroSized`): stores only a vtable, requires the
///   concrete type to be zero-sized, and derives `Copy` + `Clone`.
/// - `N > 0`: stores the value inline in `N` bytes with word alignment
///   (pinned by `DynMetadata`).
pub struct Embedded<T: ?Sized + TraitObject, const N: usize> {
    metadata: DynMetadata<T>,
    buf: [MaybeUninit<u8>; N],
}

// N == 0: vtable only — Copy + Clone (identical to old ZeroSized)
impl<T: ?Sized + TraitObject> Copy for Embedded<T, 0> {}
impl<T: ?Sized + TraitObject> Clone for Embedded<T, 0> {
    fn clone(&self) -> Self {
        *self
    }
}

impl<T: ?Sized + TraitObject, const N: usize> Deref for Embedded<T, N> {
    type Target = T;

    fn deref(&self) -> &Self::Target {
        let data = self.data_ptr();
        // SAFETY: for N == 0, size is 0 (asserted at construction) — dangling
        // ptr is fine. For N > 0, the buffer holds a valid instance.
        unsafe { &*ptr::from_raw_parts(data, self.metadata) }
    }
}

impl<T: ?Sized + TraitObject, const N: usize> DerefMut for Embedded<T, N> {
    fn deref_mut(&mut self) -> &mut Self::Target {
        let data = self.data_ptr_mut();
        // SAFETY: same invariants as Deref above.
        unsafe { &mut *ptr::from_raw_parts_mut(data, self.metadata) }
    }
}

impl<T: ?Sized + TraitObject, const N: usize> Embedded<T, N> {
    fn data_ptr(&self) -> *const () {
        if N == 0 {
            ptr::without_provenance(self.metadata.align_of())
        } else {
            self.buf.as_ptr() as *const ()
        }
    }

    fn data_ptr_mut(&mut self) -> *mut () {
        if N == 0 {
            ptr::without_provenance_mut(self.metadata.align_of())
        } else {
            self.buf.as_mut_ptr() as *mut ()
        }
    }

    /// Construct an `Embedded` from a concrete type.
    ///
    /// - `N == 0`: the concrete type must be zero-sized.
    /// - `N > 0`: the concrete type must fit within `N` bytes and have
    ///   alignment ≤ `align_of::<usize>()`.
    pub fn new<U: Debug + Copy + Unsize<T> + 'static>(val: U) -> Self {
        const {
            if N == 0 {
                assert!(
                    size_of::<U>() == 0,
                    "Embedded<_, 0> requires a zero-sized type"
                );
            } else {
                assert!(size_of::<U>() <= N, "Value too large for Embedded buffer");
                assert!(
                    align_of::<U>() <= align_of::<usize>(),
                    "Value alignment exceeds Embedded buffer alignment"
                );
            }
        }

        // Obtain vtable via unsizing coercion before the value is moved.
        let metadata = ptr::metadata(&raw const val as *const T);

        let mut this = Embedded {
            buf: [MaybeUninit::uninit(); N],
            metadata,
        };

        if N > 0 {
            // SAFETY: size and alignment checked at compile time above.
            unsafe {
                ptr::write(this.buf.as_mut_ptr() as *mut U, val);
            }
        }

        // `U: Copy` — drop is trivial.
        let _ = val;

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
