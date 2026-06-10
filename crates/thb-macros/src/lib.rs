mod derive_castable;
mod with_macro;

use proc_macro::TokenStream;

/// Derive macro implementing `Castable` for a struct, enum or union.
///
/// Adapted from trait-cast-rs (https://github.com/ink-feather-org/trait-cast-rs)
/// Licensed under MIT OR Apache-2.0
///
/// Use `#[casts_to(SomeTrait, ...)]` to specify all possible target traits
/// for which trait objects can be downcast from `dyn Castable`.
///
/// Example:
/// ```ignore
/// use thb::Castable;
///
/// #[derive(Castable)]
/// #[casts_to(Print)]
/// struct Source(i32);
///
/// trait Print {
///     fn print(&self) -> i32;
/// }
/// impl Print for Source {
///     fn print(&self) -> i32 { self.0 }
/// }
/// ```
#[proc_macro_derive(Castable, attributes(casts_to))]
pub fn derive_castable(input: TokenStream) -> TokenStream {
    derive_castable::derive_castable(input)
}

/// The `with!` proc macro provides ergonomic access to `GameObject` components
/// through the `ObjectArena`.
///
/// Syntax:
/// ```ignore
/// with!(arena_owner, |binding1, binding2, ...| { body })
/// ```
///
/// Each binding can be:
/// - `name` — bind as `&mut GameObject`
/// - `name: Type` — bind as `&mut Type` via `.need::<Type>()`
/// - `name: *Type` — copy the component via deref
/// - `name: @handle` — bind a specific handle's `GameObject`
/// - `name: Type @handle` — bind component `Type` from a specific handle
/// - `name: *Type @handle` — copy component `Type` from a specific handle
#[proc_macro]
pub fn with(input: TokenStream) -> TokenStream {
    with_macro::with(input)
}
