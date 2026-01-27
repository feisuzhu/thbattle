{
  description = "A Sanguosha board game clone, based on Touhou Project";

  inputs = {
    nixpkgs.url = "flake:nixpkgs";
    systems.url = "github:nix-systems/default";
  };

  outputs = {
    nixpkgs,
    systems,
    ...
  }: let
    eachSystem = nixpkgs.lib.genAttrs (import systems);
    pkgsFor = nixpkgs.legacyPackages;
  in {
    devShells = eachSystem (system: let
      pkgs = pkgsFor.${system};
    in {
      default = pkgs.mkShell {
        name = "thbattle-shell";
        packages = [
          pkgs.python3
          pkgs.python3Packages.uv
        ];
      };
    });
  };
}
