#include <zephyr/device.h>
#include <zephyr/drivers/gpio.h>
#include <zephyr/drivers/uart.h>
#include <zephyr/kernel.h>

static const struct device *const uart = DEVICE_DT_GET(DT_NODELABEL(uart0));
static const struct gpio_dt_spec ready = GPIO_DT_SPEC_GET(DT_ALIAS(led0), gpios);
static const struct gpio_dt_spec fault = GPIO_DT_SPEC_GET(DT_ALIAS(led1), gpios);

int main(void)
{
	const struct uart_config config = {
		.baudrate = 115200,
		.parity = UART_CFG_PARITY_NONE,
		.stop_bits = UART_CFG_STOP_BITS_1,
		.data_bits = UART_CFG_DATA_BITS_8,
		.flow_ctrl = UART_CFG_FLOW_CTRL_NONE,
	};
	unsigned char byte;

	if (!gpio_is_ready_dt(&ready) || !gpio_is_ready_dt(&fault)) {
		return 0;
	}
	if (gpio_pin_configure_dt(&ready, GPIO_OUTPUT_INACTIVE) != 0 ||
	    gpio_pin_configure_dt(&fault, GPIO_OUTPUT_ACTIVE) != 0) {
		return 0;
	}
	if (!device_is_ready(uart) || uart_configure(uart, &config) != 0) {
		return 0;
	}

	/* LED1: ready. LED2: latched fault (reset the board to retry). */
	gpio_pin_set_dt(&fault, 0);
	gpio_pin_set_dt(&ready, 1);
	for (;;) {
		int errors = uart_err_check(uart);

		if (errors != 0) {
			break;
		}
		int ret = uart_poll_in(uart, &byte);

		if (ret == 0) {
			/* Transform the response so a TX/RX short cannot falsely pass. */
			uart_poll_out(uart, byte ^ 0xa5U);
		} else if (ret == -1) {
			/* Host sends one byte at a time and waits for its response. */
			k_sleep(K_MSEC(1));
		} else {
			break;
		}
	}
	gpio_pin_set_dt(&ready, 0);
	gpio_pin_set_dt(&fault, 1);
	return 0;
}
