use std::any::Any as StdAny;
use std::fmt::Debug;

pub trait Any: StdAny + Debug {
    fn type_name(&self) -> &'static str;
}

impl<T: StdAny + Debug> Any for T {
    fn type_name(&self) -> &'static str {
        std::any::type_name::<T>()
    }
}

impl dyn Any {
    #[inline]
    pub fn is<T: 'static>(&self) -> bool {
        (self as &dyn StdAny).is::<T>()
    }

    #[inline]
    pub fn downcast_ref<T: StdAny>(&self) -> Option<&T> {
        (self as &dyn StdAny).downcast_ref::<T>()
    }

    #[inline]
    pub fn downcast_mut<T: StdAny>(&mut self) -> Option<&mut T> {
        (self as &mut dyn StdAny).downcast_mut::<T>()
    }
}
