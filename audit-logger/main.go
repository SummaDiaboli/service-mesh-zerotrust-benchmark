package main

import (
	"log"
	"github.com/gofiber/fiber/v2"
)

func main() {
	app := fiber.New()

	// Public logging endpoint
	app.Post("/log", func(c *fiber.Ctx) error {
		log.Printf("[Audit-Logger] Received log entry from %s", c.IP())
		return c.SendStatus(201)
	})

	// Private delete endpoint (INSECURE BY DESIGN for Research)
	app.Delete("/logs", func(c *fiber.Ctx) error {
		clientIP := c.IP()
		forwardedFor := c.Get("X-Forwarded-For")
		
		if forwardedFor != "" {
			clientIP = forwardedFor
			log.Printf("[Audit-Logger] ALERT: Processing DELETE with spoofed IP: %s", clientIP)
		} else {
			log.Printf("[Audit-Logger] Processing DELETE with real IP: %s", clientIP)
		}

		// Security enforcement must now be provided by the Service Mesh.
		return c.Status(200).SendString("Logs cleared successfully (Insecure)")
	})

	log.Fatal(app.Listen(":8080"))
}
