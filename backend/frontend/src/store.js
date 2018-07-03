import { Q } from '~/utils.js';

export default {
  account: null,
  refreshAccount() {
    Q(`query { me { id, phone, player { name, avatar, forumId, forumName }}}`).then(resp => {
        this.account = resp.data.me;
    });
  },
}
