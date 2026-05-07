
import discord
from discord.ext import commands
import random
import json
import asyncio
import os
import time

# ════════════════════════════════
# 🔐 TOKEN — pon tu token aquí directamente
# ════════════════════════════════
#<<<<<<< HEAD

#=======
#>>>>>>> f535446d2e35c8e82e3932b4751dfe9353aaefc6
TOKEN = os.getenv("DISCORD_TOKEN")
if not TOKEN:
    raise ValueError("❌ No se encontró DISCORD_TOKEN en las variables de entorno.")
# ════════════════════════════════
# 🏪 ID DEL SERVIDOR ADMIN
# Solo desde este servidor se pueden crear/editar/borrar items y usar comandos admin
# Clic derecho en tu servidor en Discord → Copiar ID
# ════════════════════════════════

ADMIN_GUILD_ID = 123456789012345678  # <-- PON AQUÍ EL ID DE TU SERVIDOR

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

COLOR       = discord.Color.from_rgb(0, 180, 80)
COLOR_SHOP  = discord.Color.from_rgb(255, 165, 0)
COLOR_ERROR = discord.Color.from_rgb(220, 50, 50)

# ════════════════════════════════
# 💾 BASE DE DATOS
# ════════════════════════════════

db      = {}
tienda  = {}
db_lock = asyncio.Lock()

def cargar_db():
    global db, tienda
    if os.path.exists("economia.json"):
        with open("economia.json", "r") as f:
            db = json.load(f)
    if os.path.exists("tienda.json"):
        with open("tienda.json", "r") as f:
            tienda = json.load(f)

async def guardar_db():
    async with db_lock:
        with open("economia.json", "w") as f:
            json.dump(db, f, indent=4)

async def guardar_tienda():
    async with db_lock:
        with open("tienda.json", "w") as f:
            json.dump(tienda, f, indent=4, ensure_ascii=False)

def get_user(uid):
    uid = str(uid)
    if uid not in db:
        db[uid] = {"balance": 1000, "banco": 0, "last_daily": 0, "last_trabajo": 0, "inventario": {}}
    if "last_trabajo" not in db[uid]:
        db[uid]["last_trabajo"] = 0
    if "inventario" not in db[uid]:
        db[uid]["inventario"] = {}
    return db[uid]

def generar_item_id():
    import string
    chars = string.ascii_lowercase + string.digits
    while True:
        nuevo_id = ''.join(random.choices(chars, k=6))
        if nuevo_id not in tienda:
            return nuevo_id

def es_admin_guild(ctx):
    return (
        ctx.guild is not None and
        ctx.guild.id == ADMIN_GUILD_ID and
        ctx.author.guild_permissions.administrator
    )

# ════════════════════════════════
# ❌ ERRORES
# ════════════════════════════════

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        minutos = int(error.retry_after // 60)
        segundos = int(error.retry_after % 60)
        await ctx.send(f"⏳ Espera **{minutos}m {segundos}s** para usar ese comando.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("❌ Falta un argumento. Usa `!help` para ver cómo usarlo.")
    elif isinstance(error, commands.BadArgument):
        await ctx.send("❌ Argumento inválido. Asegúrate de ingresar un número entero.")
    else:
        raise error

# ════════════════════════════════
# 📜 HELP
# ════════════════════════════════

@bot.command()
async def help(ctx):
    embed = discord.Embed(title="🎰 CASINO BOT", description="Bienvenido al casino 💎", color=COLOR)
    embed.add_field(name="💰 Economía", value=(
        "`!balance` — Ver tu saldo\n"
        "`!trabajar` — Ganar dinero (cooldown 1h)\n"
        "`!daily` — Recompensa diaria\n"
        "`!depositar <cantidad>` — Depositar al banco\n"
        "`!retirar <cantidad>` — Retirar del banco\n"
        "`!ranking` — Top 5 más ricos"
    ), inline=False)
    embed.add_field(name="🎰 Juegos", value=(
        "`!slots <apuesta>` — Máquina tragamonedas\n"
        "`!ruleta <apuesta> <rojo/negro/verde>` — Ruleta\n"
        "`!bj <apuesta>` — Blackjack interactivo\n"
        "`!coinflip <apuesta> <cara/cruz>` — Lanzar moneda\n"
        "`!dados <apuesta> <número 2-12>` — Lanzar dados"
    ), inline=False)
    embed.add_field(name="🏪 Tienda", value=(
        "`!tienda` — Ver todos los items disponibles\n"
        "`!comprar <id>` — Comprar un item\n"
        "`!inventario` — Ver tus items comprados"
    ), inline=False)
    embed.add_field(name="💸 Transferencias", value=(
        "`!enviar @usuario <cantidad>` — Enviar dinero a otro jugador"
    ), inline=False)
    if ctx.guild and ctx.guild.id == ADMIN_GUILD_ID:
        embed.add_field(name="🔧 Admin Tienda", value=(
            "`!crearitem` — Crear nuevo item (wizard interactivo)\n"
            "`!editaritem <id>` — Editar un item existente\n"
            "`!borraritem <id>` — Eliminar un item\n"
            "`!stockitem <id> <cantidad>` — Ajustar stock (-1 = ilimitado)"
        ), inline=False)
        embed.add_field(name="👑 Admin General", value=(
            "`!add-money @usuario <cantidad>` — Dar dinero a un usuario\n"
            "`!remove-money @usuario <cantidad>` — Quitar dinero a un usuario\n"
            "`!dar-item @usuario <id> [cantidad]` — Dar un item a un usuario\n"
            "`!quitar-item @usuario <id> [cantidad]` — Quitar un item a un usuario"
        ), inline=False)
    embed.set_footer(text="💡 El banco protege tu dinero de pérdidas en juegos")
    await ctx.send(embed=embed)

# ════════════════════════════════
# 💰 ECONOMÍA
# ════════════════════════════════

@bot.command()
async def balance(ctx):
    user = get_user(ctx.author.id)
    total = user["balance"] + user["banco"]
    embed = discord.Embed(title=f"💰 Balance de {ctx.author.display_name}", color=COLOR)
    embed.add_field(name="👛 Cartera", value=f"**${user['balance']:,}**", inline=True)
    embed.add_field(name="🏦 Banco",   value=f"**${user['banco']:,}**",   inline=True)
    embed.add_field(name="💎 Total",   value=f"**${total:,}**",           inline=True)
    await ctx.send(embed=embed)

@bot.command()
async def trabajar(ctx):
    user  = get_user(ctx.author.id)
    ahora = int(time.time())
    tiempo_restante = 3600 - (ahora - user["last_trabajo"])
    if tiempo_restante > 0:
        return await ctx.send(f"⏳ Debes esperar **{tiempo_restante//60}m {tiempo_restante%60}s** para volver a trabajar.")
    trabajos = [
        ("👨‍💻 Programaste una app", random.randint(300, 700)),
        ("🍕 Repartiste pizzas", random.randint(200, 400)),
        ("🎸 Tocaste en la calle", random.randint(100, 350)),
        ("📦 Trabajaste en el almacén", random.randint(250, 500)),
        ("🚗 Fuiste conductor de Uber", random.randint(200, 600)),
        ("🧹 Limpiaste oficinas", random.randint(150, 300)),
        ("📊 Hiciste consultoría", random.randint(400, 800)),
    ]
    descripcion, ganancia = random.choice(trabajos)
    user["balance"] += ganancia
    user["last_trabajo"] = ahora
    await guardar_db()
    embed = discord.Embed(title="💼 Trabajo completado", color=COLOR)
    embed.add_field(name=descripcion, value=f"Ganaste **${ganancia:,}**")
    embed.set_footer(text="Podrás trabajar de nuevo en 1 hora")
    await ctx.send(embed=embed)

@bot.command()
async def daily(ctx):
    user  = get_user(ctx.author.id)
    ahora = int(time.time())
    if ahora - user["last_daily"] < 86400:
        tiempo_restante = 86400 - (ahora - user["last_daily"])
        horas   = tiempo_restante // 3600
        minutos = (tiempo_restante % 3600) // 60
        return await ctx.send(f"⏳ Ya reclamaste tu daily. Vuelve en **{horas}h {minutos}m**.")
    user["last_daily"] = ahora
    user["balance"] += 1000
    await guardar_db()
    embed = discord.Embed(title="🎁 ¡Daily reclamado!", color=COLOR)
    embed.add_field(name="Recompensa", value="**+$1,000**")
    embed.set_footer(text="Vuelve mañana para tu siguiente daily")
    await ctx.send(embed=embed)

@bot.command()
async def depositar(ctx, cantidad: int):
    user = get_user(ctx.author.id)
    if cantidad <= 0:
        return await ctx.send("❌ La cantidad debe ser mayor a 0.")
    if cantidad > user["balance"]:
        return await ctx.send(f"❌ No tienes suficiente. Tu cartera: **${user['balance']:,}**")
    user["balance"] -= cantidad
    user["banco"]   += cantidad
    await guardar_db()
    await ctx.send(f"🏦 Depositaste **${cantidad:,}** al banco. Banco: **${user['banco']:,}**")

@bot.command()
async def retirar(ctx, cantidad: int):
    user = get_user(ctx.author.id)
    if cantidad <= 0:
        return await ctx.send("❌ La cantidad debe ser mayor a 0.")
    if cantidad > user["banco"]:
        return await ctx.send(f"❌ No tienes suficiente en el banco. Banco: **${user['banco']:,}**")
    user["banco"]   -= cantidad
    user["balance"] += cantidad
    await guardar_db()
    await ctx.send(f"💸 Retiraste **${cantidad:,}** del banco. Cartera: **${user['balance']:,}**")

@bot.command()
async def ranking(ctx):
    if not db:
        return await ctx.send("📊 No hay datos aún.")
    top = sorted(db.items(), key=lambda x: x[1]["balance"] + x[1]["banco"], reverse=True)[:5]
    embed    = discord.Embed(title="🏆 Top 5 Más Ricos", color=COLOR)
    medallas = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]
    for i, (uid, data) in enumerate(top):
        try:
            u = await bot.fetch_user(int(uid))
            nombre = u.display_name
        except Exception:
            nombre = f"Usuario {uid}"
        embed.add_field(name=f"{medallas[i]} {nombre}", value=f"**${data['balance']+data['banco']:,}**", inline=False)
    await ctx.send(embed=embed)

# ════════════════════════════════
# 🏪 TIENDA
# ════════════════════════════════

@bot.command(name="tienda")
async def ver_tienda(ctx):
    if not tienda:
        return await ctx.send(embed=discord.Embed(title="🏪 Tienda", description="La tienda está vacía por ahora. ¡Vuelve más tarde!", color=COLOR_SHOP))
    embed = discord.Embed(title="🏪 Tienda del Casino", description="Usa `!comprar <id>` para adquirir un item.", color=COLOR_SHOP)
    for item_id, item in tienda.items():
        stock_txt = "∞ Ilimitado" if item["stock"] == -1 else f"{item['stock']} disponibles"
        embed.add_field(
            name=f"{item['emoji']} {item['nombre']}  •  `{item_id}`",
            value=f"📝 {item['descripcion']}\n💰 **${item['precio']:,}** — 📦 {stock_txt}",
            inline=False
        )
    embed.set_footer(text="💡 El ID está entre backticks junto al nombre del item")
    await ctx.send(embed=embed)

@bot.command()
async def comprar(ctx, item_id: str):
    item_id = item_id.lower()
    if item_id not in tienda:
        return await ctx.send(f"❌ No existe ningún item con ID `{item_id}`. Usa `!tienda` para ver los disponibles.")
    item = tienda[item_id]
    user = get_user(ctx.author.id)
    if item["stock"] == 0:
        return await ctx.send(f"❌ El item **{item['nombre']}** está agotado.")
    if user["balance"] < item["precio"]:
        return await ctx.send(f"❌ No tienes suficiente.\nPrecio: **${item['precio']:,}** — Tu cartera: **${user['balance']:,}**")
    user["balance"] -= item["precio"]
    user["inventario"][item_id] = user["inventario"].get(item_id, 0) + 1
    if item["stock"] != -1:
        tienda[item_id]["stock"] -= 1
    await guardar_db()
    await guardar_tienda()
    embed = discord.Embed(title="✅ ¡Compra realizada!", color=COLOR)
    embed.add_field(name=f"{item['emoji']} {item['nombre']}", value=f"Pagaste **${item['precio']:,}**\nCartera restante: **${user['balance']:,}**", inline=False)
    embed.set_footer(text="Usa !inventario para ver tus items")
    await ctx.send(embed=embed)

@bot.command()
async def inventario(ctx):
    user = get_user(ctx.author.id)
    inv  = user.get("inventario", {})
    if not inv:
        return await ctx.send("🎒 Tu inventario está vacío. ¡Ve a la `!tienda`!")
    embed = discord.Embed(title=f"🎒 Inventario de {ctx.author.display_name}", color=COLOR)
    for item_id, cantidad in inv.items():
        if item_id in tienda:
            item = tienda[item_id]
            embed.add_field(name=f"{item['emoji']} {item['nombre']} × {cantidad}", value=f"_{item['descripcion']}_", inline=False)
        else:
            embed.add_field(name=f"❓ Item desconocido × {cantidad}", value=f"ID: `{item_id}` (eliminado de la tienda)", inline=False)
    await ctx.send(embed=embed)

# ════════════════════════════════
# 🔧 ADMIN — CREAR ITEM (wizard)
# ════════════════════════════════

@bot.command()
async def crearitem(ctx):
    if not es_admin_guild(ctx):
        return await ctx.send("❌ Este comando solo puede usarse en el servidor autorizado.")
    await ctx.send(embed=discord.Embed(
        title="🔧 Crear nuevo item",
        description="Vamos a crear un item paso a paso.\nTienes **60 segundos** en cada paso.\nEscribe `cancelar` para abortar.",
        color=COLOR_SHOP
    ))
    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel
    async def pedir(pregunta):
        if pregunta:
            await ctx.send(pregunta)
        try:
            msg = await bot.wait_for("message", timeout=60.0, check=check)
        except asyncio.TimeoutError:
            await ctx.send("⏰ Tiempo agotado. Cancelado.")
            return None
        if msg.content.lower() == "cancelar":
            await ctx.send("🚫 Creación cancelada.")
            return None
        return msg.content.strip()

    nombre = await pedir("**[1/5]** ¿Cómo se llama el item?")
    if nombre is None: return
    emoji = await pedir("**[2/5]** ¿Qué emoji tiene el item?")
    if emoji is None: return
    descripcion = await pedir("**[3/5]** Escribe una descripción corta:")
    if descripcion is None: return

    while True:
        precio_str = await pedir("**[4/5]** ¿Cuánto cuesta? (número entero)")
        if precio_str is None: return
        try:
            precio = int(precio_str)
            if precio <= 0: await ctx.send("❌ Debe ser mayor a 0."); continue
            break
        except ValueError:
            await ctx.send("❌ Escribe un número válido.")

    while True:
        stock_str = await pedir("**[5/5]** ¿Cuántas unidades en stock? (`-1` = ilimitado)")
        if stock_str is None: return
        try:
            stock = int(stock_str)
            if stock < -1 or stock == 0: await ctx.send("❌ Número positivo o -1 para ilimitado."); continue
            break
        except ValueError:
            await ctx.send("❌ Escribe un número válido.")

    stock_txt = "∞ Ilimitado" if stock == -1 else str(stock)
    embed_confirm = discord.Embed(title="📋 Confirmar nuevo item", description="¿Todo correcto? Responde **sí** o **no**.", color=COLOR_SHOP)
    embed_confirm.add_field(name="Nombre",     value=f"{emoji} {nombre}", inline=True)
    embed_confirm.add_field(name="Precio",     value=f"${precio:,}",       inline=True)
    embed_confirm.add_field(name="Stock",      value=stock_txt,            inline=True)
    embed_confirm.add_field(name="Descripción",value=descripcion,          inline=False)
    await ctx.send(embed=embed_confirm)

    confirmacion = await pedir("")
    if confirmacion is None: return
    if confirmacion.lower() not in ["sí", "si", "yes", "s", "y"]:
        return await ctx.send("🚫 Creación cancelada.")

    item_id = generar_item_id()
    tienda[item_id] = {"nombre": nombre, "emoji": emoji, "descripcion": descripcion, "precio": precio, "stock": stock}
    await guardar_tienda()
    await ctx.send(f"✅ Item **{emoji} {nombre}** creado con ID `{item_id}`.\nYa aparece en `!tienda`.")

# ════════════════════════════════
# 🔧 ADMIN — EDITAR ITEM
# ════════════════════════════════

@bot.command()
async def editaritem(ctx, item_id: str):
    if not es_admin_guild(ctx):
        return await ctx.send("❌ Este comando solo puede usarse en el servidor autorizado.")
    item_id = item_id.lower()
    if item_id not in tienda:
        return await ctx.send(f"❌ No existe ningún item con ID `{item_id}`.")
    item = tienda[item_id]
    embed = discord.Embed(title=f"✏️ Editar item `{item_id}`", description=(
        f"Item actual: **{item['emoji']} {item['nombre']}**\n\n"
        "¿Qué quieres editar?\n"
        "1️⃣ Nombre | 2️⃣ Emoji | 3️⃣ Descripción | 4️⃣ Precio | 5️⃣ Stock | ❌ Cancelar"
    ), color=COLOR_SHOP)
    msg = await ctx.send(embed=embed)
    opciones = {"1️⃣": "nombre", "2️⃣": "emoji", "3️⃣": "descripcion", "4️⃣": "precio", "5️⃣": "stock", "❌": "cancelar"}
    for e in opciones: await msg.add_reaction(e)
    try:
        reaction, _ = await bot.wait_for("reaction_add", timeout=30.0,
            check=lambda r, u: u == ctx.author and str(r.emoji) in opciones and r.message.id == msg.id)
    except asyncio.TimeoutError:
        return await ctx.send("⏰ Tiempo agotado.")
    campo = opciones[str(reaction.emoji)]
    if campo == "cancelar":
        return await ctx.send("🚫 Edición cancelada.")
    await ctx.send(f"✏️ Escribe el nuevo valor para **{campo}**:")
    try:
        resp = await bot.wait_for("message", timeout=60.0, check=lambda m: m.author == ctx.author and m.channel == ctx.channel)
    except asyncio.TimeoutError:
        return await ctx.send("⏰ Tiempo agotado.")
    nuevo_valor = resp.content.strip()
    if campo in ("precio", "stock"):
        try:
            nuevo_valor = int(nuevo_valor)
            if campo == "precio" and nuevo_valor <= 0: return await ctx.send("❌ El precio debe ser mayor a 0.")
            if campo == "stock" and (nuevo_valor < -1 or nuevo_valor == 0): return await ctx.send("❌ Stock debe ser positivo o -1.")
        except ValueError:
            return await ctx.send("❌ Debes escribir un número entero.")
    tienda[item_id][campo] = nuevo_valor
    await guardar_tienda()
    await ctx.send(f"✅ Campo **{campo}** del item `{item_id}` actualizado.")

# ════════════════════════════════
# 🔧 ADMIN — BORRAR ITEM
# ════════════════════════════════

@bot.command()
async def borraritem(ctx, item_id: str):
    if not es_admin_guild(ctx):
        return await ctx.send("❌ Este comando solo puede usarse en el servidor autorizado.")
    item_id = item_id.lower()
    if item_id not in tienda:
        return await ctx.send(f"❌ No existe ningún item con ID `{item_id}`.")
    item = tienda[item_id]
    msg = await ctx.send(f"⚠️ ¿Seguro que quieres eliminar **{item['emoji']} {item['nombre']}** (`{item_id}`)?\nReacciona ✅ para confirmar o ❌ para cancelar.")
    await msg.add_reaction("✅"); await msg.add_reaction("❌")
    try:
        reaction, _ = await bot.wait_for("reaction_add", timeout=20.0,
            check=lambda r, u: u == ctx.author and str(r.emoji) in ["✅", "❌"] and r.message.id == msg.id)
    except asyncio.TimeoutError:
        return await ctx.send("⏰ Tiempo agotado.")
    if str(reaction.emoji) == "❌":
        return await ctx.send("🚫 Eliminación cancelada.")
    del tienda[item_id]
    await guardar_tienda()
    await ctx.send(f"🗑️ Item `{item_id}` eliminado.")

# ════════════════════════════════
# 🔧 ADMIN — AJUSTAR STOCK
# ════════════════════════════════

@bot.command()
async def stockitem(ctx, item_id: str, cantidad: int):
    if not es_admin_guild(ctx):
        return await ctx.send("❌ Este comando solo puede usarse en el servidor autorizado.")
    item_id = item_id.lower()
    if item_id not in tienda:
        return await ctx.send(f"❌ No existe ningún item con ID `{item_id}`.")
    if cantidad < -1 or cantidad == 0:
        return await ctx.send("❌ El stock debe ser un número positivo o -1 (ilimitado).")
    tienda[item_id]["stock"] = cantidad
    await guardar_tienda()
    stock_txt = "∞ Ilimitado" if cantidad == -1 else f"{cantidad} unidades"
    await ctx.send(f"📦 Stock de **{tienda[item_id]['emoji']} {tienda[item_id]['nombre']}** actualizado a **{stock_txt}**.")

# ════════════════════════════════
# 💸 ENVIAR DINERO
# ════════════════════════════════

@bot.command()
async def enviar(ctx, objetivo: discord.Member, cantidad: int):
    if objetivo.bot:
        return await ctx.send("❌ No puedes enviar dinero a un bot.")
    if objetivo == ctx.author:
        return await ctx.send("❌ No puedes enviarte dinero a ti mismo.")
    if cantidad <= 0:
        return await ctx.send("❌ La cantidad debe ser mayor a 0.")
    remitente = get_user(ctx.author.id)
    receptor  = get_user(objetivo.id)
    if cantidad > remitente["balance"]:
        return await ctx.send(f"❌ No tienes suficiente.\nCartera: **${remitente['balance']:,}** — Intentas enviar: **${cantidad:,}**")
    msg = await ctx.send(f"💸 ¿Confirmas enviar **${cantidad:,}** a {objetivo.mention}?\nReacciona ✅ para confirmar o ❌ para cancelar.")
    await msg.add_reaction("✅"); await msg.add_reaction("❌")
    try:
        reaction, _ = await bot.wait_for("reaction_add", timeout=20.0,
            check=lambda r, u: u == ctx.author and str(r.emoji) in ["✅", "❌"] and r.message.id == msg.id)
    except asyncio.TimeoutError:
        return await ctx.send("⏰ Tiempo agotado. Transferencia cancelada.")
    if str(reaction.emoji) == "❌":
        return await ctx.send("🚫 Transferencia cancelada.")
    remitente["balance"] -= cantidad
    receptor["balance"]  += cantidad
    await guardar_db()
    embed = discord.Embed(title="💸 Transferencia realizada", color=COLOR)
    embed.add_field(name="De",       value=ctx.author.mention,   inline=True)
    embed.add_field(name="Para",     value=objetivo.mention,     inline=True)
    embed.add_field(name="Cantidad", value=f"**${cantidad:,}**", inline=True)
    embed.add_field(name="Tu nueva cartera", value=f"**${remitente['balance']:,}**", inline=False)
    await ctx.send(embed=embed)

# ════════════════════════════════
# 👑 ADMIN — ADD/REMOVE MONEY
# ════════════════════════════════

@bot.command(name="add-money")
async def add_money(ctx, objetivo: discord.Member, cantidad: int):
    if not es_admin_guild(ctx): return await ctx.send("❌ Este comando solo puede usarse en el servidor autorizado.")
    if objetivo.bot: return await ctx.send("❌ No puedes dar dinero a un bot.")
    if cantidad <= 0: return await ctx.send("❌ La cantidad debe ser mayor a 0.")
    user = get_user(objetivo.id)
    user["balance"] += cantidad
    await guardar_db()
    embed = discord.Embed(title="👑 Dinero añadido", color=COLOR)
    embed.add_field(name="Usuario",       value=objetivo.mention,            inline=True)
    embed.add_field(name="Añadido",       value=f"**+${cantidad:,}**",       inline=True)
    embed.add_field(name="Nueva cartera", value=f"**${user['balance']:,}**", inline=True)
    await ctx.send(embed=embed)

@bot.command(name="remove-money")
async def remove_money(ctx, objetivo: discord.Member, cantidad: int):
    if not es_admin_guild(ctx): return await ctx.send("❌ Este comando solo puede usarse en el servidor autorizado.")
    if objetivo.bot: return await ctx.send("❌ No puedes quitar dinero a un bot.")
    if cantidad <= 0: return await ctx.send("❌ La cantidad debe ser mayor a 0.")
    user = get_user(objetivo.id)
    if cantidad > user["balance"]:
        return await ctx.send(f"❌ {objetivo.display_name} solo tiene **${user['balance']:,}** en cartera.")
    user["balance"] -= cantidad
    await guardar_db()
    embed = discord.Embed(title="👑 Dinero eliminado", color=COLOR_ERROR)
    embed.add_field(name="Usuario",       value=objetivo.mention,            inline=True)
    embed.add_field(name="Eliminado",     value=f"**-${cantidad:,}**",       inline=True)
    embed.add_field(name="Nueva cartera", value=f"**${user['balance']:,}**", inline=True)
    await ctx.send(embed=embed)

# ════════════════════════════════
# 👑 ADMIN — DAR/QUITAR ITEMS
# ════════════════════════════════

@bot.command(name="dar-item")
async def dar_item(ctx, objetivo: discord.Member, item_id: str, cantidad: int = 1):
    if not es_admin_guild(ctx): return await ctx.send("❌ Este comando solo puede usarse en el servidor autorizado.")
    if objetivo.bot: return await ctx.send("❌ No puedes dar items a un bot.")
    item_id = item_id.lower()
    if item_id not in tienda: return await ctx.send(f"❌ No existe ningún item con ID `{item_id}`.")
    if cantidad <= 0: return await ctx.send("❌ La cantidad debe ser mayor a 0.")
    item = tienda[item_id]
    user = get_user(objetivo.id)
    user["inventario"][item_id] = user["inventario"].get(item_id, 0) + cantidad
    await guardar_db()
    embed = discord.Embed(title="🎁 Item otorgado", color=COLOR)
    embed.add_field(name="Usuario",  value=objetivo.mention,                    inline=True)
    embed.add_field(name="Item",     value=f"{item['emoji']} {item['nombre']}", inline=True)
    embed.add_field(name="Cantidad", value=f"× {cantidad}",                    inline=True)
    await ctx.send(embed=embed)

@bot.command(name="quitar-item")
async def quitar_item(ctx, objetivo: discord.Member, item_id: str, cantidad: int = 1):
    if not es_admin_guild(ctx): return await ctx.send("❌ Este comando solo puede usarse en el servidor autorizado.")
    if objetivo.bot: return await ctx.send("❌ No puedes quitar items a un bot.")
    item_id = item_id.lower()
    if item_id not in tienda: return await ctx.send(f"❌ No existe ningún item con ID `{item_id}`.")
    if cantidad <= 0: return await ctx.send("❌ La cantidad debe ser mayor a 0.")
    user = get_user(objetivo.id)
    inv  = user["inventario"]
    if item_id not in inv or inv[item_id] < cantidad:
        return await ctx.send(f"❌ {objetivo.display_name} solo tiene **{inv.get(item_id, 0)}** unidades de ese item.")
    inv[item_id] -= cantidad
    if inv[item_id] == 0: del inv[item_id]
    await guardar_db()
    item = tienda[item_id]
    embed = discord.Embed(title="🗑️ Item quitado", color=COLOR_ERROR)
    embed.add_field(name="Usuario",  value=objetivo.mention,                    inline=True)
    embed.add_field(name="Item",     value=f"{item['emoji']} {item['nombre']}", inline=True)
    embed.add_field(name="Cantidad", value=f"× {cantidad}",                    inline=True)
    await ctx.send(embed=embed)

# ════════════════════════════════
# 🎰 SLOTS
# ════════════════════════════════

@bot.command()
async def slots(ctx, apuesta: int):
    user = get_user(ctx.author.id)
    if apuesta <= 0: return await ctx.send("❌ La apuesta debe ser mayor a 0.")
    if apuesta > user["balance"]: return await ctx.send(f"❌ No tienes suficiente. Cartera: **${user['balance']:,}**")
    user["balance"] -= apuesta
    simbolos  = ["🍒", "🍋", "💎", "7️⃣", "⭐", "🍇"]
    resultado = [random.choice(simbolos) for _ in range(3)]
    if resultado[0] == resultado[1] == resultado[2]:
        if resultado[0] == "💎":   mult, texto = 10, "💎 **MEGA JACKPOT**"
        elif resultado[0] == "7️⃣": mult, texto =  7, "7️⃣ **JACKPOT**"
        else:                       mult, texto =  5, "🎉 **TRIPLE**"
        ganancia = apuesta * mult
        user["balance"] += ganancia
        resultado_texto = f"✅ +${ganancia:,}"
    elif resultado[0]==resultado[1] or resultado[1]==resultado[2] or resultado[0]==resultado[2]:
        ganancia = int(apuesta * 1.5)
        user["balance"] += ganancia
        texto = "✨ Par encontrado"
        resultado_texto = f"✅ +${ganancia:,}"
    else:
        texto = "😢 Sin premio"
        resultado_texto = f"❌ -${apuesta:,}"
    await guardar_db()
    embed = discord.Embed(title="🎰 Tragamonedas", color=COLOR)
    embed.add_field(name="Resultado", value=" | ".join(resultado), inline=False)
    embed.add_field(name=texto,       value=resultado_texto,        inline=False)
    embed.set_footer(text=f"Cartera: ${user['balance']:,}")
    await ctx.send(embed=embed)

# ════════════════════════════════
# 🎡 RULETA
# ════════════════════════════════

@bot.command()
async def ruleta(ctx, apuesta: int, color: str):
    user = get_user(ctx.author.id)
    if apuesta <= 0: return await ctx.send("❌ La apuesta debe ser mayor a 0.")
    if apuesta > user["balance"]: return await ctx.send(f"❌ No tienes suficiente. Cartera: **${user['balance']:,}**")
    color = color.lower()
    if color not in ["rojo", "negro", "verde"]: return await ctx.send("❌ Elige: `rojo`, `negro` o `verde`")
    user["balance"] -= apuesta
    numero = random.randint(0, 36)
    if numero == 0:          resultado, emoji_r = "verde", "🟢"
    elif numero % 2 == 0:    resultado, emoji_r = "negro", "⚫"
    else:                    resultado, emoji_r = "rojo",  "🔴"
    if color == resultado:
        ganancia = apuesta * 14 if resultado == "verde" else apuesta * 2
        user["balance"] += ganancia
        texto = f"✅ Ganaste **+${ganancia:,}**"
    else:
        texto = f"❌ Perdiste **-${apuesta:,}**"
    await guardar_db()
    embed = discord.Embed(title="🎡 Ruleta", color=COLOR)
    embed.add_field(name="Número",     value=f"**{numero}** {emoji_r} {resultado}", inline=False)
    embed.add_field(name="Tu apuesta", value=f"{color} — {texto}",                  inline=False)
    embed.set_footer(text=f"Cartera: ${user['balance']:,}")
    await ctx.send(embed=embed)

# ════════════════════════════════
# 🃏 BLACKJACK
# ════════════════════════════════

MAZO = [2,3,4,5,6,7,8,9,10,10,10,10,11] * 4

def sacar_carta(mano): return mano + [random.choice(MAZO)]
def valor_mano(mano):
    total = sum(mano); ases = mano.count(11)
    while total > 21 and ases: total -= 10; ases -= 1
    return total
def mano_str(mano): return " | ".join(str(c) for c in mano) + f" = **{valor_mano(mano)}**"

@bot.command()
async def bj(ctx, apuesta: int):
    user = get_user(ctx.author.id)
    if apuesta <= 0: return await ctx.send("❌ La apuesta debe ser mayor a 0.")
    if apuesta > user["balance"]: return await ctx.send(f"❌ No tienes suficiente. Cartera: **${user['balance']:,}**")
    user["balance"] -= apuesta
    await guardar_db()
    mano_jugador = sacar_carta(sacar_carta([]))
    mano_dealer  = sacar_carta(sacar_carta([]))
    def make_embed(estado="jugando"):
        embed = discord.Embed(title="🃏 Blackjack", color=COLOR)
        embed.add_field(name="Tu mano", value=mano_str(mano_jugador), inline=False)
        if estado == "jugando":
            embed.add_field(name="Dealer", value=f"{mano_dealer[0]} | ❓", inline=False)
            embed.set_footer(text="Reacciona: ✅ Pedir carta | ❌ Plantarse")
        else:
            embed.add_field(name="Dealer", value=mano_str(mano_dealer), inline=False)
        return embed
    if valor_mano(mano_jugador) == 21:
        ganancia = int(apuesta * 2.5); user["balance"] += ganancia; await guardar_db()
        embed = make_embed("fin"); embed.add_field(name="🎴 ¡BLACKJACK!", value=f"+${ganancia:,}", inline=False)
        return await ctx.send(embed=embed)
    msg = await ctx.send(embed=make_embed())
    await msg.add_reaction("✅"); await msg.add_reaction("❌")
    while True:
        try:
            reaction, _ = await bot.wait_for("reaction_add", timeout=30.0,
                check=lambda r, u: u == ctx.author and str(r.emoji) in ["✅","❌"] and r.message.id == msg.id)
        except asyncio.TimeoutError:
            await msg.edit(content="⏰ Tiempo agotado. Te plantaste automáticamente."); break
        if str(reaction.emoji) == "✅":
            mano_jugador = sacar_carta(mano_jugador)
            if valor_mano(mano_jugador) > 21:
                await msg.edit(embed=make_embed("fin"), content="")
                embed = discord.Embed(title="🃏 Blackjack", color=discord.Color.red())
                embed.add_field(name="💥 Te pasaste", value=f"Perdiste **-${apuesta:,}**")
                await ctx.send(embed=embed); return
            await msg.edit(embed=make_embed())
        else: break
    while valor_mano(mano_dealer) < 17: mano_dealer = sacar_carta(mano_dealer)
    pj = valor_mano(mano_jugador); pd = valor_mano(mano_dealer)
    await msg.edit(embed=make_embed("fin"))
    if pd > 21 or pj > pd:
        ganancia = apuesta * 2; user["balance"] += ganancia; resultado = f"✅ ¡Ganaste **+${ganancia:,}**!"
    elif pj == pd:
        user["balance"] += apuesta; resultado = f"🤝 Empate. Recuperas **${apuesta:,}**"
    else:
        resultado = f"❌ Perdiste **-${apuesta:,}**"
    await guardar_db()
    embed = discord.Embed(title="🃏 Resultado", color=COLOR)
    embed.add_field(name="Tú", value=str(pj), inline=True)
    embed.add_field(name="Dealer", value=str(pd), inline=True)
    embed.add_field(name="Resultado", value=resultado, inline=False)
    embed.set_footer(text=f"Cartera: ${user['balance']:,}")
    await ctx.send(embed=embed)

# ════════════════════════════════
# 🪙 COINFLIP
# ════════════════════════════════

@bot.command()
async def coinflip(ctx, apuesta: int, eleccion: str):
    user = get_user(ctx.author.id)
    if apuesta <= 0: return await ctx.send("❌ La apuesta debe ser mayor a 0.")
    if apuesta > user["balance"]: return await ctx.send(f"❌ No tienes suficiente. Cartera: **${user['balance']:,}**")
    eleccion = eleccion.lower()
    if eleccion not in ["cara", "cruz"]: return await ctx.send("❌ Elige `cara` o `cruz`")
    user["balance"] -= apuesta
    resultado = random.choice(["cara", "cruz"])
    if eleccion == resultado:
        ganancia = apuesta * 2; user["balance"] += ganancia; texto = f"✅ ¡Ganaste **+${ganancia:,}**!"
    else:
        texto = f"❌ Perdiste **-${apuesta:,}**"
    await guardar_db()
    emoji_r = "👑" if resultado == "cara" else "🦅"
    embed = discord.Embed(title="🪙 Coinflip", color=COLOR)
    embed.add_field(name=f"{emoji_r} Salió: **{resultado}**", value=texto, inline=False)
    embed.set_footer(text=f"Cartera: ${user['balance']:,}")
    await ctx.send(embed=embed)

# ════════════════════════════════
# 🎲 DADOS
# ════════════════════════════════

@bot.command()
async def dados(ctx, apuesta: int, numero: int):
    user = get_user(ctx.author.id)
    if apuesta <= 0: return await ctx.send("❌ La apuesta debe ser mayor a 0.")
    if apuesta > user["balance"]: return await ctx.send(f"❌ No tienes suficiente. Cartera: **${user['balance']:,}**")
    if numero < 2 or numero > 12: return await ctx.send("❌ Elige un número entre 2 y 12.")
    user["balance"] -= apuesta
    d1 = random.randint(1, 6); d2 = random.randint(1, 6); total = d1 + d2
    if total == numero:
        mult = {2:10,3:8,4:6,5:5,6:4,7:3,8:4,9:5,10:6,11:8,12:10}[numero]
        ganancia = apuesta * mult; user["balance"] += ganancia
        texto = f"✅ ¡Ganaste **+${ganancia:,}** (x{mult})!"
    else:
        texto = f"❌ Perdiste **-${apuesta:,}**"
    await guardar_db()
    embed = discord.Embed(title="🎲 Dados", color=COLOR)
    embed.add_field(name="Resultado",  value=f"🎲 {d1} + 🎲 {d2} = **{total}**", inline=False)
    embed.add_field(name="Tu número",  value=str(numero),                          inline=True)
    embed.add_field(name="Resultado",  value=texto,                                inline=False)
    embed.set_footer(text=f"Cartera: ${user['balance']:,}")
    await ctx.send(embed=embed)

# ════════════════════════════════
# 🚀 ON READY
# ════════════════════════════════

@bot.event
async def on_ready():
    cargar_db()
    print(f"✅ {bot.user} conectado")
    print(f"📡 Servidores: {len(bot.guilds)}")
    print(f"🏪 Items en tienda: {len(tienda)}")
    print(f"🔒 Servidor admin: {ADMIN_GUILD_ID}")

bot.run(TOKEN)
