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
        devShell = {
          default = pkgs.mkShell {
            name = "thbattle-shell";
            packages = [
              pkgs.uv
              (
                pkgs.python3.withPackages
                (
                  ps:
                    with ps; let
                      runtime = [
                        gevent
                        requests
                        raven
                        websocket-client
                        msgpack
                      ];
                      dev = [
                        coverage
                        itsdangerous
                      ];
                    in
                      runtime ++ dev
                )
              )
            ];
          };
        };
      }
    );
}
