# Discord Art Bot
_A cool Discord bot that converts images to emoji art_

![Showcase](https://imgur.com/YjsYK3l.png)
Credit for this picture and the beautifully drawn mask goes to [KoleckOLP](https://github.com/KoleckOLP/)

## Features

Supports **dithering**, **arbitrary image and output sizes** and a **variety of emojis**:
- **Circle** emojis (see above)
- **Square** emojis
- **Heart** emojis
- **Food** emojis (yes, food emojis)

## How to use

Summon this bot with `$art` and an image file attached.

Several optional parameters are possible (case-insensitive, order doesn't matter):
- **An integer number** sets the converted image's size in emojis-per-row<br/>_(default is 20)_
- **circle**, **square**, **heart** or **food** sets the emoji type used for the conversion<br/>_(default is circle)_
- **outputimage** makes the bot output its temporary image<br/>_(disabled by default)_

Use `$art abort` (or `$art stop` or `$art cancel`) to interrupt the drawing process.

### Example commands
- `$art 20 square`
- `$art 100 outputimage circle`
- `$art 50 food`

## Examples
<img src="https://imgur.com/HVCjtmx.png" width=33%><img src="https://imgur.com/Ci0BSr5.png" width=33%><img src="https://imgur.com/Gpzajqr.png" width=33%>
<img src="https://imgur.com/mkhqp5q.png" width=33%><img src="https://imgur.com/U0aTxry.png" width=33%><img src="https://imgur.com/E7TJi7x.png" width=33%>
