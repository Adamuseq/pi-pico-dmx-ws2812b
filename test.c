#include "pico/stdlib.h"
#include "hardware/uart.h"
#include "pico/multicore.h"
#include "pico/neopixel.h"

#define UART_ID uart0
#define DMX_CHANNEL_COUNT 512
#define NUM_LEDS 16
#define LED_PIN 0 // The Neopixel data pin on the Pico

volatile uint8_t dmxData[DMX_CHANNEL_COUNT];
volatile bool dmxDataReceived = false;
volatile uint16_t startAddress = 1; // Default start address

void uart_isr() {
    // Read data from UART FIFO and store it in the dmxData array
    for (int i = 0; i < DMX_CHANNEL_COUNT; i++) {
        dmxData[i] = uart_getc(UART_ID);
    }

    // Indicate that DMX data has been received
    dmxDataReceived = true;
}

void neopixel_task() {
    // Initialize Neopixel
    neopixel_init(pio0, 0, LED_PIN, NUM_LEDS);
    uint32_t colors[NUM_LEDS];

    while (true) {
        if (dmxDataReceived) {
            // Process DMX data starting from the specified start address (3 channels per LED - R, G, B)
            for (int led = 0; led < NUM_LEDS; led++) {
                int dmxIndex = (startAddress - 1 + led) * 3; // Adjusted start address
                uint8_t r = dmxData[dmxIndex];
                uint8_t g = dmxData[dmxIndex + 1];
                uint8_t b = dmxData[dmxIndex + 2];
                colors[led] = pio_encode_rgb888(r, g, b);
            }

            // Show the updated colors on Neopixels
            neopixel_push_mask(pio0, 1 << 0, colors, NUM_LEDS);

            // Clear the flag
            dmxDataReceived = false;
        }
    }
}

int main() {
    stdio_init_all();

    // Initialize UART with DMX512 settings (250000 baud, 8N2)
    uart_init(UART_ID, 250000);
    uart_set_format(UART_ID, 8, 2);

    // Set up the UART RX pin and enable the UART interrupt
    gpio_set_function(1, GPIO_FUNC_UART);
    uart_set_irq_enables(UART_ID, true, false);

    // Enable the UART RX interrupt
    irq_set_exclusive_handler(UART0_IRQ, uart_isr);
    irq_set_enabled(UART0_IRQ, true);

    // Start the Neopixel task on the second core
    multicore_launch_core1(neopixel_task);

    while (true) {
        // Your main loop can perform other tasks if needed
    }

    return 0;
}
