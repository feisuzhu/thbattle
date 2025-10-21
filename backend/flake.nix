{
  description = "Flake for thbattle backend";

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
        overlay = final: prev: {
          pythonPackagesExtensions =
            prev.pythonPackagesExtensions
            ++ [
              (
                python-final: python-prev: {
                  django-redis-sessions = python-prev.buildPythonPackage rec {
                    pname = "django-redis-sessions";
                    version = "0.6.2";
                    format = "setuptools";
                    src = prev.fetchPypi {
                      inherit pname version format;
                      hash = "sha256-ujPsyhmPKN3DLZ8DdC3I38NMGFe3icdeqEJdbX1zdr4=";
                    };
                    doCheck = false;
                  };
                  django-schema-graph = python-prev.buildPythonPackage rec {
                    pname = "django-schema-graph";
                    version = "3.1.0";
                    format = "wheel";
                    # nativeBuildInputs = [python-prev.poetry-core];
                    # src = prev.fetchFromGitHub {
                    #   owner = "meshy";
                    #   repo = pname;
                    #   rev = "v${version}";
                    #   hash = "sha256-YmBsSl3AWDgLSNL6Zfmdg6m8AzNKbOsTjsSbVwPQIA4=";
                    # };
                    src = prev.fetchurl {
                      url = "https://files.pythonhosted.org/packages/e3/3b/df3825ad4693b69fa7fa95d654e4672992029d5d698813f3e80cc6c38da7/django_schema_graph-${version}-py3-none-any.whl";
                      hash = "sha256-skDjCEFAGECeFYjKZaCxBPGbOCkwPjkHHpqoW4YxfT0=";
                    };
                    # postPatch = ''
                    #   substituteInPlace pyproject.toml \
                    #     --replace-fail 'poetry>=0.12' 'poetry-core>=1.0.0' \
                    #     --replace-fail 'poetry.masonry.api' 'poetry.core.masonry.api'
                    #   '';
                    propagatedBuildInputs = with python-final; [
                      cattrs
                      attrs
                    ];
                    doCheck = false;
                  };
                }
              )
            ];
        };
        pkgs = nixpkgs.legacyPackages.${system}.extend overlay;
      in {
        overlays.default = overlay;
        packages = {
          default = pkgs.callPackage ./default.nix {};
        };

        devShells = {
          default = pkgs.mkShell {
            name = "thb-backend-shell";
            packages = [
              pkgs.uv
              (
                pkgs.python3.withPackages
                (
                  ps:
                    with ps; [
                      redis
                      requests
                      raven
                      gunicorn
                      django
                      graphene
                      django-annoying
                      graphene-django
                      django-redis-sessions
                      itsdangerous
                      msgpack
                      pymysql
                      pyyaml
                      django-schema-graph
                      trueskill
                      qrcode
                      pillow
                      sentry-sdk
                      pytz
                      psycopg
                      greenlet
                    ]
                )
              )
            ];
          };
        };
      }
    );
}
