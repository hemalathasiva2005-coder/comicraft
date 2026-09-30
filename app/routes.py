from pathlib import Path

from fastapi import (
    APIRouter,
    Form,
    HTTPException,
    Request
)

from fastapi.responses import (
    HTMLResponse,
    FileResponse,
    JSONResponse
)

from fastapi.templating import (
    Jinja2Templates
)


from app.schemas import (
    PromptRequest
)

from app.gemini_flash import (
    generate_outline
)

from app.gemini_pro import (
    generate_story
)

from app.image_generator import (
    generate_image
)

from app.layout_builder import (
    build_comic_layout
)

from app.exporters import (
    save_pdf
)


router = APIRouter()


templates = Jinja2Templates(
    directory="templates"
)


def create_comic(
    request_data
):

    # STEP 1
    # Generate 5-panel outline

    outline = generate_outline(

        request_data.story_prompt,

        request_data.character_name,

        request_data.setting,

        request_data.tone,

        request_data.art_style
    )


    # STEP 2
    # Generate narration and dialogue

    story = generate_story(

        outline,

        request_data.character_name,

        request_data.tone
    )


    # STEP 3
    # Generate images

    image_paths = []


    for panel in outline:

        image_path = generate_image(

            panel["image_prompt"],

            panel["panel_number"],

            request_data.art_style
        )


        image_paths.append(
            image_path
        )


    # STEP 4
    # Build layout

    layout = build_comic_layout(

        outline,

        story,

        image_paths
    )


    # STEP 5
    # Generate PDF

    pdf_path = save_pdf(
        layout
    )


    return layout, pdf_path


# -----------------------------------
# HOME
# -----------------------------------

@router.get(
    "/",
    response_class=HTMLResponse
)
async def home(
    request: Request
):

    return templates.TemplateResponse(

        "index.html",

        {
            "request": request
        }
    )


# -----------------------------------
# GENERATE COMIC
# -----------------------------------

@router.post(
    "/generate",
    response_class=HTMLResponse
)
async def generate(

    request: Request,

    story_prompt: str = Form(...),

    character_name: str = Form(...),

    setting: str = Form(...),

    tone: str = Form(...),

    art_style: str = Form(...)
):

    try:

        data = PromptRequest(

            story_prompt=story_prompt,

            character_name=character_name,

            setting=setting,

            tone=tone,

            art_style=art_style
        )


        layout, pdf_path = create_comic(
            data
        )


        return templates.TemplateResponse(

            "comic_preview.html",

            {

                "request": request,

                "layout": layout,

                "pdf_path": pdf_path,

                "story_input":
                    data.model_dump()
            }
        )


    except Exception as error:

        return templates.TemplateResponse(

            "index.html",

            {

                "request": request,

                "error": str(error)
            },

            status_code=500
        )


# -----------------------------------
# JSON API
# -----------------------------------

@router.post(
    "/generate-comic/json"
)
async def generate_json(
    data: PromptRequest
):

    try:

        layout, pdf_path = create_comic(
            data
        )


        return JSONResponse({

            "success": True,

            "panels": layout,

            "pdf_path": pdf_path
        })


    except Exception as error:

        raise HTTPException(

            status_code=500,

            detail=str(error)
        )


# -----------------------------------
# TEST IMAGE
# -----------------------------------

@router.get(
    "/test-image"
)
async def test_image(

    prompt: str =
        "A brave fox exploring "
        "an enchanted forest"
):

    try:

        image_path = generate_image(

            prompt,

            1,

            "comic book"
        )


        return {

            "success": True,

            "image_path": image_path
        }


    except Exception as error:

        raise HTTPException(

            status_code=500,

            detail=str(error)
        )


# -----------------------------------
# DOWNLOAD PDF
# -----------------------------------

@router.get(
    "/download/{filename}"
)
async def download_pdf(
    filename: str
):

    base = Path(
        "static/exports"
    ).resolve()


    target = (
        base / filename
    ).resolve()


    if (

        target.parent != base

        or target.suffix.lower() != ".pdf"

        or not target.exists()

    ):

        raise HTTPException(

            status_code=404,

            detail="PDF not found."
        )


    return FileResponse(

        target,

        media_type="application/pdf",

        filename=target.name
    )


# -----------------------------------
# EXPORT SUCCESS
# -----------------------------------

@router.get(
    "/export-success",
    response_class=HTMLResponse
)
async def export_success(

    request: Request,

    pdf: str = ""
):

    return templates.TemplateResponse(

        "export_success.html",

        {

            "request": request,

            "pdf_path": pdf
        }
    )