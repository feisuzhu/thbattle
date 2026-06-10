// Adapted from trait-cast-rs (https://github.com/ink-feather-org/trait-cast-rs)
// Licensed under MIT OR Apache-2.0

use proc_macro::TokenStream;
use quote::quote;
use syn::{
    DeriveInput, Error, Token, TypePath,
    parse::{self, Parse, ParseStream},
    parse_macro_input,
    punctuated::Punctuated,
};

/// Helper struct to parse attribute arguments like `#[casts_to(Ident, Ident, ...)]`.
struct CastTargets {
    targets: Vec<TypePath>,
}

impl Parse for CastTargets {
    fn parse(input: ParseStream<'_>) -> parse::Result<Self> {
        let targets: Vec<TypePath> = Punctuated::<TypePath, Token![,]>::parse_terminated(input)?
            .into_iter()
            .collect();
        Ok(Self { targets })
    }
}

impl quote::ToTokens for CastTargets {
    fn to_tokens(&self, tokens: &mut proc_macro2::TokenStream) {
        let vars = &self.targets;
        tokens.extend(quote!(#(#vars),*));
    }
}

pub fn derive_castable(input: TokenStream) -> TokenStream {
    let derive_input = parse_macro_input!(input as DeriveInput);
    let source_ident = &derive_input.ident;

    let casts_to_attr = derive_input
        .attrs
        .iter()
        .find(|attr| attr.path().is_ident("casts_to"));

    let cast_targets = if let Some(attr) = casts_to_attr {
        match attr.parse_args::<CastTargets>() {
            Ok(targets) => targets,
            Err(err) => {
                return Error::new_spanned(
                    attr,
                    format!("Failed to parse casts_to attribute: {err}"),
                )
                .to_compile_error()
                .into();
            }
        }
    } else {
        return Error::new_spanned(
            derive_input.ident,
            "Missing required attribute 'casts_to', e.g. #[casts_to(TargetTrait1, TargetTrait2)]",
        )
        .to_compile_error()
        .into();
    };

    TokenStream::from(quote!(
        crate::utils::traitcast::make_castable_decl! {
            #source_ident => (#cast_targets)
        }
    ))
}
