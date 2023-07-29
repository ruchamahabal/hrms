<template>
    <ion-page>
        <ion-content>
            <h2>Hello{{ geolocation }}</h2>
        </ion-content>
    </ion-page>
</template>

<script setup>
import { IonPage, IonContent } from '@ionic/vue';

import { ref } from 'vue';

let geolocation = ref("")

// const showPosition = (position) => {
//     geolocation.value = "Latitude: " + position?.coords.latitude +
//         "<br>Longitude: " + position?.coords.longitude;
// }


navigator.geolocation.getCurrentPosition((position) => geolocation.value = position.coords.latitude + " " + position.coords.longitude);

</script>