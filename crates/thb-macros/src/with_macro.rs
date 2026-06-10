use proc_macro::TokenStream;
use proc_macro2::{TokenStream as TokenStream2, TokenTree};
use quote::{format_ident, quote, ToTokens};
use syn::{
    parse::{Parse, ParseStream},
    parse_macro_input,
    punctuated::Punctuated,
    Block, Expr, Ident, Token, Type,
};

enum Kind {
    Object,
    Need(Type),
}

struct Binding {
    name: Ident,
    handle: Expr,
    kind: Kind,
    deref: bool,
}

struct Input {
    arena_owner: Expr,
    bindings: Vec<Binding>,
    body: Block,
}

fn parse_handle_until_delim(input: ParseStream) -> syn::Result<Expr> {
    let mut tokens = TokenStream2::new();
    while !input.is_empty() && !input.peek(Token![,]) && !input.peek(Token![|]) {
        let tt: TokenTree = input.parse()?;
        tokens.extend(std::iter::once(tt));
    }
    if tokens.is_empty() {
        return Err(input.error("expected handle expression after `@`"));
    }
    syn::parse2::<Expr>(tokens)
}

impl Parse for Binding {
    fn parse(input: ParseStream) -> syn::Result<Self> {
        let name: Ident = input.parse()?;

        let mut explicit_handle: Option<Expr> = None;
        let mut kind = Kind::Object;

        let mut deref = false;

        if input.peek(Token![:]) {
            input.parse::<Token![:]>()?;

            if input.peek(Token![@]) {
                input.parse::<Token![@]>()?;
                explicit_handle = Some(parse_handle_until_delim(input)?);
            } else {
                if input.peek(Token![*]) {
                    input.parse::<Token![*]>()?;
                    deref = true;
                }
                let ty: Type = input.parse()?;
                kind = Kind::Need(ty);

                if input.peek(Token![@]) {
                    input.parse::<Token![@]>()?;
                    explicit_handle = Some(parse_handle_until_delim(input)?);
                }
            }
        }

        let handle =
            explicit_handle.unwrap_or_else(|| syn::parse_quote_spanned!(name.span()=> #name));

        Ok(Binding { name, handle, kind, deref })
    }
}

impl Parse for Input {
    fn parse(input: ParseStream) -> syn::Result<Self> {
        let arena_owner: Expr = input.parse()?;
        input.parse::<Token![,]>()?;

        input.parse::<Token![|]>()?;
        let bindings_punct: Punctuated<Binding, Token![,]> =
            Punctuated::parse_separated_nonempty(input)?;
        input.parse::<Token![|]>()?;

        let body: Block = input.parse()?;

        Ok(Input {
            arena_owner,
            bindings: bindings_punct.into_iter().collect(),
            body,
        })
    }
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
pub fn with(input: TokenStream) -> TokenStream {
    let Input {
        arena_owner,
        bindings,
        body,
    } = parse_macro_input!(input as Input);

    let mut groups: Vec<Vec<usize>> = Vec::new();
    let mut group_handle_text: Vec<String> = Vec::new();
    for (idx, b) in bindings.iter().enumerate() {
        let key = b.handle.to_token_stream().to_string();
        match group_handle_text.iter().position(|k| k == &key) {
            Some(g) => groups[g].push(idx),
            None => {
                group_handle_text.push(key);
                groups.push(vec![idx]);
            }
        }
    }

    for group in &groups {
        let object_binding_count = group
            .iter()
            .filter(|&&i| matches!(bindings[i].kind, Kind::Object))
            .count();
        if object_binding_count > 0 && group.len() > 1 {
            let span = bindings[group[0]].name.span();
            return syn::Error::new(
                span,
                "a handle bound as `&mut GameObject` cannot share its handle with other bindings; \
                 split into separate `with!` calls or remove the duplicate",
            )
            .to_compile_error()
            .into();
        }
    }

    let group_idents: Vec<Ident> = (0..groups.len())
        .map(|i| format_ident!("__with_obj_{}", i))
        .collect();

    let group_handles: Vec<&Expr> = groups.iter().map(|g| &bindings[g[0]].handle).collect();

    let mut post_stmts: Vec<TokenStream2> = Vec::new();

    for (group, obj_ident) in groups.iter().zip(group_idents.iter()) {
        if group.len() == 1 {
            let b = &bindings[group[0]];
            let name = &b.name;
            match &b.kind {
                Kind::Object => {
                    post_stmts.push(quote! { let #name = #obj_ident; });
                }
                Kind::Need(ty) => {
                    if b.deref {
                        post_stmts.push(quote! {
                            let #name: #ty = *#obj_ident.need::<#ty>();
                        });
                    } else {
                        post_stmts.push(quote! {
                            let #name: &mut #ty = #obj_ident.need::<#ty>();
                        });
                    }
                }
            }
        } else {
            let inner_tys: Vec<&Type> = group
                .iter()
                .map(|&i| match &bindings[i].kind {
                    Kind::Need(t) => t,
                    Kind::Object => unreachable!(),
                })
                .collect();

            let n = group.len();
            let method = format_ident!("need{}", n);

            let names: Vec<&Ident> = group.iter().map(|&i| &bindings[i].name).collect();
            let tmp_names: Vec<Ident> = names
                .iter()
                .map(|n| format_ident!("__with_ref_{}", n))
                .collect();

            post_stmts.push(quote! {
                let ( #( #tmp_names ),* ): ( #( &mut #inner_tys ),* ) =
                    #obj_ident.#method::< #( #inner_tys ),* >();
            });

            for (gi, &i) in group.iter().enumerate() {
                let b = &bindings[i];
                let name = &b.name;
                let ty = match &b.kind {
                    Kind::Need(t) => t,
                    Kind::Object => unreachable!(),
                };
                let tmp = &tmp_names[gi];
                if b.deref {
                    post_stmts.push(quote! { let #name: #ty = *#tmp; });
                } else {
                    post_stmts.push(quote! { let #name: &mut #ty = #tmp; });
                }
            }
        }
    }

    let body_stmts = &body.stmts;

    let expanded = quote! {{
        let [ #( #group_idents ),* ] = (#arena_owner).arena.reference([ #( #group_handles ),* ]);
        #( #post_stmts )*
        { #( #body_stmts )* }
    }};

    expanded.into()
}
