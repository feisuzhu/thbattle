# frontend

## 目前需要实现的功能

- 登录是通过 query string 中的短时 token 实现的，然后前端通过这个 token 请求后端获取长时 token，用于后续的请求。
- 如果没有短时 token，则查看有没有本地缓存的长时 token，如果有则使用，没有则跳转到登录页面（或者跳转到一个说明页面，提示在游戏中登录）。
- 界面的设计可以抄米游社（只是个参考，如果有自己的想法可以直接按照自己的想法来），大概好看就可以
- 功能：展示玩家资料，修改玩家资料
  - 昵称、头像、个性签名等等。
- 功能：从旧论坛迁移
  - 迁移游戏数
  - 发勋章（勋章里包含老 UID）
  - 选择是不是迁移老昵称（新注册的时候老昵称是保留的）(主要是为了这个）


This template should help get you started developing with Vue 3 in Vite.

## Recommended IDE Setup

[VSCode](https://code.visualstudio.com/) + [Volar](https://marketplace.visualstudio.com/items?itemName=Vue.volar) (and disable Vetur).

## Type Support for `.vue` Imports in TS

TypeScript cannot handle type information for `.vue` imports by default, so we replace the `tsc` CLI with `vue-tsc` for type checking. In editors, we need [Volar](https://marketplace.visualstudio.com/items?itemName=Vue.volar) to make the TypeScript language service aware of `.vue` types.

## Customize configuration

See [Vite Configuration Reference](https://vite.dev/config/).

## Project Setup

```sh
npm install
```

### Compile and Hot-Reload for Development

```sh
npm run dev
```

### Type-Check, Compile and Minify for Production

```sh
npm run build
```

### Lint with [ESLint](https://eslint.org/)

```sh
npm run lint
```
