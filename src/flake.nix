{
  description = "A Sanguosha board game clone, based on Touhou Project";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs?ref=nixos-unstable";
    utils.url = "github:numtide/flake-utils";
  };

  outputs = {
    nixpkgs,
    utils,
    ...
  }:
    utils.lib.eachDefaultSystem (
      system: let
        pkgs = nixpkgs.legacyPackages.${system};
      in {
        devShell = pkgs.mkShell {
          buildInputs = [
            pkgs.uv
            (pkgs.python3Minimal.withPackages
              (ps:
                with ps; [
                  gevent
                  requests
                  raven
                  websocket-client
                  msgpack
                ]))
          ];
        };
      }
    );
}
