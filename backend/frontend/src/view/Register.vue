<template>
  <section class="section">
    <div class="container">
      <div class="columns">
        <div class="column is-three-quarters content">
          <h2><i class="fas fa-arrow-circle-right"></i> 开始玩 THB 之前你需要知道的事</h2>
          <ol>
            <li>东方符斗祭（aka. THB，THBattle，以下简称 THB）游戏本体免费，未来也不会出现影响游戏平衡的收费项目。</li>
            <li>THB 会不定期出一些周边产品，如果可以的话还请多支持。</li>
            <li>THB 在目前所有流行的平台上都有客户端，包括 Windows/macOS/Linux/Android/iOS</li>
          </ol>
          <hr>
          <h2><i class="fas fa-arrow-circle-right"></i> 关于社区氛围的说明</h2>
          <ol>
            <li>THB 一直以来都是一个小社区，玩家们在这里交朋友的有很多，社区氛围一直良好。</li>
            <li>这里没有一个明确可以遵守的守则，但是有一个原则：请不要把你的恶意泼洒在这里，请小心维护有爱的社区氛围。</li>
            <li>因为是免费游戏，黑幕组对破坏社区氛围的行为绝不会手软，阈值很低处罚严厉。</li>
            <li>常见的破坏社区氛围的行为：辱骂、恶意游戏（鞭尸、故意不按身份出牌、挂机）。</li>
          </ol>
          <hr>
          <h2><i class="fas fa-arrow-circle-right"></i> 关于注册和绑定论坛帐号的说明</h2>
          <ol>
            <li>注册需要手机号，一个手机号只能注册一个帐号。</li>
            <li>游戏中的昵称不可以与其他人重复，不可以是常见人物名称（如“风见幽香”）。</li>
            <li>老用户绑定论坛帐号后，论坛的 id 、名称以及之前的节操、游戏数、掉线数、勋章会保留。</li>
            <li>绑定论坛帐号只能进行一次，不可逆。</li>
            <li>一个论坛帐号只能绑定一个游戏帐号。</li>
          </ol>
        </div>

        <div class="column" v-if="store.account">
          <div class="box">
            <p><strong>注册成功了</strong></p>
            <p>手机：{{ store.account.phone }}</p>
            <p>昵称：{{ store.account.player.name }}</p>
            <p>绑定的论坛ID：{{ store.account.player.forumId }}</p>
            <p>绑定的论坛昵称：{{ store.account.player.forumName }}</p>
            <p>&nbsp;</p>
            <p>如果要注册新帐号，请退出后再注册。</p>
          </div>
        </div>

        <div class="column" v-else>
          <fancy-input label="手机"
                       type="text"
                       v-model="phone"
                       icon="fa-mobile-alt"
                       placeholder="18866666666"
                       :status="phoneStatus"
                       :help="phoneHelp"
                       @input="refreshAvailability(), touched.phone = true">
            <button class="button is-info"
               :disabled="smscodeRequested >= 0 || !availability.phone ? 'disabled' : false"
               @click="requestSmscode()">
               {{ smscodeRequested >= 0 ? '(' + smscodeRequested + ')' : '获取验证码' }}
            </button>
          </fancy-input>

          <fancy-input label="验证码"
                       type="text"
                       v-model="smscode"
                       icon="fa-barcode"
                       placeholder="6位数字"
                       :status="smscodeStatus"
                       @input="touched.smscode = true" />

          <fancy-input label="游戏昵称"
                       type="text"
                       v-model="name"
                       icon="fa-address-card"
                       placeholder="补魔的黑蔷薇"
                       :status="nameStatus"
                       :help="nameHelp"
                       @input="refreshAvailability(), touched.name = true" />

          <fancy-input label="密码"
                       type="password"
                       v-model="password"
                       icon="fa-key"
                       placeholder="密码一定要长"
                       :status="passwordStatus"
                       @input="touched.password = true" />

          <div class="control">
            <button class="button is-link">注册</button>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>
<!--
<style lang="sass">
</style>
-->
<script>
import debounce from 'lodash.debounce';

import { Q }  from '~/utils.js';
import Store from '~/store.js';

import FancyInput from '~/components/common/FancyInput.vue';

export default {
  name: 'Login',
  data() {
    return {
        store: Store,

        phone: '',
        password: '',
        name: '',
        smscode: '',

        availability: {
          phone: undefined,
          name: undefined,
        },
        errors: {
          phone: undefined,
          name: undefined,
        },
        touched: {
          phone: undefined,
          smscode: undefined,
          name: undefined,
          password: undefined,
        },

        smscodeRequested: -1,
    };
  },
  methods: {
    refreshAvailability: debounce(async function() {
      var resp = await Q(`
        query ($phone: String, $name: String) {
          availability {
            phone(phone: $phone)
            name(name: $name)
          }
        }
      `, { phone: this.phone, name: this.name });

      this.errors = (resp.errors || [])
        .map(e => [e.path[e.path.length-1], e.message])
        .reduce((a, [k, v]) => (a[k] = v, a), {});

      this.availability = Object.entries(resp.data.availability)
        .map(v => [v[0], !!v[1]])
        .reduce((a, [k, v]) => (a[k] = v, a), {});
    }, 200),

    async requestSmscode() {
      var resp = await Q(`mutation ($phone: String!) { system { smsCode(phone: $phone) }}`, {phone: this.phone});
      if(resp.errors) {
        this.availability.phone = false;
        this.errors.phone = resp.errors[0].message;
        return;
      }
      this.smscodeRequested = 60;
      var handle = setInterval(() => {
        if(this.smscodeRequested-- < 0) {
          clearInterval(handle);
        }
      }, 1000);
    },
  },
  computed: {
    phoneStatus() { return this.touched.phone && this.availability.phone; },
    phoneHelp() { return !this.touched.phone ? '' : this.availability.phone ? '手机号可用' : this.errors.phone || '手机号不可用'; },
    smscodeStatus() { return this.touched.smscode && !!/^\d{6}$/.test(this.smscode); },
    smscodeHelp() { return ''; },
    nameStatus() { return this.touched.name && this.availability.name; },
    nameHelp() { return !this.touched.name ? '' : this.availability.name ? '昵称可用' : this.errors.name || '昵称不可用'; },
    passwordStatus() { return this.touched.password && !!this.password; },
    passwordHelp() { return ''; },
  },
  components: { FancyInput },
}
</script>
