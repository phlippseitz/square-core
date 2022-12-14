<!-- The Main View -->
<template>
  <div id="app" class="d-flex flex-column h-100">
    <NavBar
        v-on:sign-in="signIn"
        v-on:sign-up="signUp"
        v-on:account="account"
        v-on:sign-out="signOut" />
    <main class="flex-fill" :class="{ 'my-4': !isLandingPage }">
      <router-view :keycloak="keycloak" class="h-100" :class="{ 'container-xxl': !isLandingPage }" />
    </main>
    <Footer />
  </div>
</template>

<script>
import Vue from 'vue'
import NavBar from '@/components/NavBar.vue'
import Footer from '@/components/Footer.vue'

export default Vue.component('app', {
  props: ['keycloak', 'requiresAuthentication'],
  components: {
    NavBar,
    Footer
  },
  data() {
    return {
      publicPath: process.env.BASE_URL
    }
  },
  computed: {
    isLandingPage() {
      return this.$route.name === 'home'
    }
  },
  methods: {
    signIn() {
      this.keycloak.login({ redirectUri: `${window.location.origin}` })
    },
    signUp() {
      this.keycloak.register({ redirectUri: `${window.location.origin}` })
    },
    signOut() {
      this.$store.dispatch('signOut').then(() => {
        this.keycloak.logout({ redirectUri: `${window.location.origin}` })
      })
    },
    account() {
      this.keycloak.accountManagement()
    }
  },
  watch: {
    $route() {
      // Users do not have a visible link to protected sites so they usually will never see this redirect
      // Using browser history or entering a direct URL can result in this view
      // The redirect to an intermediate site is required to protect against some infinite redirect cycles
      if (!this.keycloak.authenticated && 'requiresAuthentication' in this.$route.meta && this.$route.meta.requiresAuthentication) {
        this.$router.push('/signin')
      }
    }
  },
  beforeMount() {
    if (this.keycloak.authenticated) {
      this.keycloak.loadUserInfo().then(userInfo => {
        this.$store.dispatch('signIn', { userInfo: userInfo })
      })
    } else {
      this.$store.dispatch('signOut')
    }
  }
})
</script>

<style lang='scss'>
    $primary: #006691;
    $success: #089e7b;
    $info: #43afde;
    $warning: #deac16;
    $danger: #de4516;
    @import "~bootstrap/scss/bootstrap";

    main .container-xl, .modal-header, .modal-body {
      padding-left: max(var(--bs-gutter-x, 0.75rem), env(safe-area-inset-left));
      padding-right: max(var(--bs-gutter-x, 0.75rem), env(safe-area-inset-right));
    }
    .bg-gradient {
      background-image: linear-gradient(0, rgba(255, 255, 255, 0.15), rgba(255, 255, 255, 0)) !important;
    }
    .feature-icon {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      width: 4rem;
      height: 4rem;
      margin-bottom: 1rem;
      font-size: 2rem;
      color: #fff;
      border-radius: .75rem;
    }
    .card-columns {
      column-gap: 2em;
      @include media-breakpoint-up(sm) {
        column-count: 2;
      }
      @include media-breakpoint-up(lg) {
        column-count: 3;
      }
    }
    @media (max-width: 512px) {
      .input-group {
        display: inline-block;
      }
      .input-group .btn, .input-group .form-control, .input-group .form-select {
        width: 100%;
      }
      .input-group .form-control, .input-group .form-select {
        border: 1px solid #ced4da !important;
        border-radius: 0.25rem !important;
      }
      .input-group .btn {
        height: calc(3.5rem + 2px);
        min-height: calc(1.5em + 0.75rem + 2px);
        margin: 0.75rem auto !important;
        border-radius: 0.3rem !important;
      }
    }
</style>
