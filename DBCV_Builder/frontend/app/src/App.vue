<template>
  <div>
    <router-view />
  </div>
</template>

<script setup></script>

<style>
*,
:after,
:before {
  box-sizing: border-box;
  margin: 0;
  font-family: 'Inter', Helvetica, Arial, sans-serif;
  letter-spacing: 0.07em;
}

i::before {
  font-family: 'Font Awesome 7 Free' !important;
}

body {
  color: #fff;
}

html {
  padding: 0;
  margin: 0;
  background: transparent;
}

button,
a {
  color: #fff;
  background: transparent;
  border: 0;
  padding: 0;
  margin: 0;
  cursor: pointer;
  text-decoration: none;
}

textarea:focus,
textarea:focus-visible,
input:focus,
input:focus-visible,
select:focus,
select:focus-visible {
  outline: 0;
  border: 0;
}

ul {
  list-style-type: none;
  padding: 0;
  margin: 0;
}

.error {
  color: red !important;
  font-size: 12px;
}
</style>
