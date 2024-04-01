"""Welcome to Reflex! This file outlines the steps to create a basic app."""

import io
import reflex as rx
import anthropic
import base64
import PIL
from PIL.Image import Image


prompt = """
You are a website roaster. Your job is to look at images of webpages and make fun of the design with a score from 1 to 10 for each of the following criteria: design, usability, originality, and overall. You can also provide feedback on how to improve the website.
You should be a very harsh and nasty critic (in a comical way), finding flaws where there are none and being overly critical. The goal is to make the user laugh. Be very rude and sarcastic, no matter how good the site is.

Here is an example of how to format your critique:
Design: 4
Usability: 3
Originality: 5
Overall: 2
Feedback: Not bad, if this is the best you can do. But I've seen better websites made by a 5-year-old. The colors are too bright and the layout is all over the place.

Do not include any other information in your critique. Remember, the goal is to be funny and sarcastic and rude, I shouldn't hear any compliments in your critique.
Don't use any cliches like "pack up and go home" or "designed by a toddler." Be original and creative in your insults.
"""


class State(rx.State):
    """The app state."""
    image: Image = PIL.Image.new("RGB", (10, 10))
    processing: bool
    design: int
    usability: int
    originality: int
    overall: int
    feedback: str

    def run_model(self):
        # Process the image with the model.
        client = anthropic.Anthropic()
        image = io.BytesIO()
        self.image.save(image, format='PNG')
        image = image.getvalue()
        image_media_type = "image/png"
        image3_data = base64.b64encode(image).decode("utf-8")
        try:
            message = client.messages.create(
                model="claude-3-haiku-20240307",
                temperature=0.999,
                max_tokens=1024,
                system=prompt,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": image_media_type,
                                    "data": image3_data,
                                },
                            },
                        ],
                    }
                ],
            )
            critique = message.content[0].text

            # Extract the critique from the message
            self.design = int(critique.split("\n")[0].split(":")[1].strip())
            self.usability = int(critique.split("\n")[1].split(":")[1].strip())
            self.originality = int(critique.split("\n")[2].split(":")[1].strip())
            self.overall = int(critique.split("\n")[3].split(":")[1].strip())
            self.feedback = critique.split("Feedback:")[1].strip()
        finally:
            self.processing = False

    async def generate_code(self, files: list[rx.UploadFile]):
        image = await files[0].read()
        self.image = PIL.Image.open(io.BytesIO(image))
        self.processing = True
        yield State.run_model

def logo():
    return rx.center(
        rx.link(
            rx.hstack(
                "Built with ",
                rx.image(src="/Reflex.svg"),
                text_align="center",
                align="center",
                padding="1em",
            ),
            href="https://reflex.dev",
        ),
        width="100%",
    )


def card(title: str, score: int):
    return rx.card(
        rx.heading(title, size="4"),
        rx.hstack(
            rx.text(f"{score} / 10"),
            rx.chakra.circular_progress(value=score, max_=10, track_color=str(rx.color("accent", 7))),
        ),
    )

def index() -> rx.Component:
    return rx.container(
        rx.vstack(
            rx.heading("Roast My Website", size="8"),
            rx.upload(
                rx.flex(
                    rx.icon("upload", width="48", height="48"),
                    rx.text("Upload an image of your webpage", as_="p", size="3"),
                    rx.text("or", as_="p", size="2"),
                    rx.button("Browse files", variant="soft"),
                    direction="column",
                    align="center",
                    justify="center",
                    gap="4px",
                ),
                border_radius="8px",
                padding="24px",
                width="100%",
                min_height="200px",
                id="upload",
                border=f"1px dashed {rx.color('accent')}",
            ),
            rx.hstack(
                rx.cond(
                    State.processing,
                    rx.chakra.circular_progress(is_indeterminate=True),
                    rx.button(
                        "Critique",
                        on_click=[State.generate_code(rx.upload_files(upload_id="upload"))],
                        size="4",
                    ),
                ),
                rx.vstack(rx.foreach(rx.selected_files("upload"), rx.text)),
                align="center",
            ),
            rx.cond(
                State.image,
                rx.image(src=State.image),
            ),
            rx.cond(
                State.feedback,
                rx.vstack(
                    rx.grid(
                        *[
                            card(title, score)
                            for title, score in [
                                ("Design", State.design),
                                ("Usability", State.usability),
                                ("Originality", State.originality),
                                ("Overall", State.overall),
                            ]
                        ],
                        columns="2",
                        width="100%",
                    ),
                    rx.callout(State.feedback, size="3"),
                ),
            ),
            rx.spacer(),
            logo(),
            spacing="5",
            min_height="100vh",
            padding="2em",
            padding_top="4em",
            background_color="white",
        ),
        size="3",
    )


app = rx.App(theme=rx.theme(accent_color="indigo"), style={
    "background_color": rx.color("accent", 4)
})
app.add_page(index)
