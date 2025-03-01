import { defineStore } from 'pinia'
import { useQuery } from 'villus';
import { graphql } from '@/scripts/graphql';
import { computed } from 'vue';

const defaultValue = () => ({
  id: -1,
  name: "",
  bio: "",
  avatar: "",
  prefs: "",

  level: 0,
  exp: 0,
  up: 0,
  bomb: 0,
  point: 0,

  games: 0,
  drops: 0
})

export const useProfileStore = defineStore('profile', () => {
  const { data, isFetching, execute } = useQuery({
    query: graphql(`
    query($token: String!){
      player(token: $token) {
        id
        name
        bio
        avatar
        prefs
        
        level
        exp
        up
        bomb
        point

        games
        drops
      }
    }`),
  });

  const profile = computed(() => data.value?.player || defaultValue());

  return {
    profile,
    isFetching,
    fetch: execute,
  };
})
