---
layout: post
title: Unreal Engine development workflow using just VSCode
tags: unreal
description: How to setup VSCode as a light C++ IDE for developing and debugging projects with the Unreal Engine
---

A good part of my day consits of waiting for Visual Studio (VS) to respond. I work with Unreal Engine (UE) on Windows and VS seems to be the recommended IDE for it, even though it's not really required by UE or its build system in any way. There are many other IDE choices out there, but I tend to use VSCode for other projects and note-taking, so I wanted to try exclusively using it for UE as well, and this is what I got.

I think this post could be useful even if you don't plan on doing exactly this, as we'll end up setting up, building, cooking, packaging, and etc. manually "from the command line", and you can probably use some of that in order to create/enhance your own setup.

This post goes over the main aspects of the setup first, and at the end ties them all together into a clear-cut step-by-step, which sort of works as a TL;DR too.

# VSCode workspace

First of all, it's handy to have some workspace-specific settings, so I recommend setting up an actual VSCode workspace. I use a single workspace directly on the UE install root (so next to the GenerateProjectFiles.bat and Setup.bat scripts), and add the folders for each individual UE project. The VSCode workspace JSON file looks like this:

``` json
{
	"folders": [
		{
			"path": "."
		},
		{
			"path": "F:/MyProject/"
		}
	],
	"settings": {
		"editor.tabSize": 4,
		"editor.insertSpaces": false,
		"editor.glyphMargin": true,
		"git.enabled": false,
		"files.exclude": {
			"**/.cache": true
		},
		"search.exclude": {
			"**/Intermediate/*": true,
			".vs/*": true,
			".cache/*": true,
			".vscode/*": true,
			"**/*.dll": true,
			"**/*.ilk": true,
			"**/*.pdb": true,
			"**/*.exe": true,
			"**/*.uasset": true
		},
		"files.watcherExclude": {
			"**/Intermediate/*": true,
			".vs/*": true,
			".cache/*": true,
			".vscode/*": true,
			"**/*.dll": true,
			"**/*.ilk": true,
			"**/*.pdb": true,
			"**/*.exe": true,
			"**/*.uasset": true
		},
		"clangd.arguments": [
			"-j=16",
			"--pch-storage=memory",
			"--clang-tidy",
			"--rename-file-limit=0",
			"--background-index"
		]
	}
}
```

Note that we're specifying that indenting should be done with tabs, and that they should be 4 spaces wide. This because this setup will follow [Epic's coding standard](https://docs.unrealengine.com/5.1/en-US/epic-cplusplus-coding-standard-for-unreal-engine/) as closely as possible, which uses that. Other than the indentation, you can see I excluded a bunch of filetypes from showing up on search and from being watched, although I didn't exclude them from the explorer view (the `files.exclude` entry is for that), since I want to be able to see all files there at all times.

Ignore the "clangd" bit for now, we'll get there!

# VSCode tasks

VSCode let's you setup [tasks](https://code.visualstudio.com/Docs/editor/tasks) for automating any commands. It's slightly better than keeping a bunch of batch scripts on-hand, since you can easily specify dependencies between them, have them show up on VSCode's UI and can easily bind keyboad shortcuts. You can see the official docs for more details, but the TL;DR way to set them up is to make a ".vscode" folder on your workspace root (so next to the Engine folder), and to put a "tasks.json" file in there.

We're going to be adding a lot of tasks here for everything you may want to do, but for now a valid "tasks.json" just looks like the below:

``` json
{
	// See https://go.microsoft.com/fwlink/?LinkId=733558
	// for the documentation about the tasks.json format
	"version": "2.0.0",
	"tasks": [
	]
}
```

# Setting up clangd

Unreal uses a custom build system with a lot of code generation, and the source files expect the include paths to be a certain way (relative to the modules), so overall I couldn't get VSCode Intellisense to work with it. Clangd does actually work though, so here we'll set it up for UE.

Download and install the latest stable release of [LLVM](https://github.com/llvm/llvm-project/releases). I'm using version 16.0.0. It should come with clangd bundled in (open a terminal and type `clangd --version` after the install to check), but you can install it directly [here](https://github.com/clangd/clangd/releases) if that's not the case for some reason.

You will now need to install the [clangd extension](https://marketplace.visualstudio.com/items?itemName=llvm-vs-code-extensions.vscode-clangd) for VSCode as well, so that it can use your clangd install for syntax highlighting, formatting and etc.

Clangd uses clang (a C++ compiler) and compiles your code under the hood, so in order to get clangd working on the UE source code and your project, you need to generate a file that tells clang how to compile everything. Luckily Unreal Build Tool (UBT) (which is UE's build system) can do that! We're going to setup a few VSCode tasks for that, so our "tasks.json" will look like this now:

``` json
{
	// See https://go.microsoft.com/fwlink/?LinkId=733558
	// for the documentation about the tasks.json format
	"version": "2.0.0",
	"tasks": [
		{
			"label": "Build UAT",
			"detail": "Builds the Unreal Automation Tool (which also builds UBT). Most other commands require this be built beforehand",
			"type": "shell",
			"command": "${workspaceFolder}/Engine/Build/BatchFiles/BuildUAT.bat",
			"group": "build",
			"presentation": {
				"reveal": "always",
				"showReuseMessage": false
			},
			"promptOnClose": false,
			"problemMatcher": "$msCompile",
		},
		{
			"label": "Regenerate compile_commands.json for the Unreal Editor",
			"detail": "Regenerates compile_commands.json and the .rsp.gcd files used by clangd",
			"type": "shell",
			"command": "${workspaceFolder}/Engine/Binaries/DotNET/AutomationTool/UnrealBuildTool.exe",
			"args": [
				"-mode=GenerateClangDatabase",
				"UnrealEditor",
				"Development",
				"Win64"
			],
			"group": "build",
			"presentation": {
				"reveal": "always",
				"showReuseMessage": false
			},
			"promptOnClose": false,
			"problemMatcher": "$msCompile",
			"dependsOrder": "sequence",
			"dependsOn": ["Build UAT"]
		},
		{
			"label": "Regenerate compile_commands.json for Project",
			"detail": "Regenerates compile_commands.json and the .rsp.gcd files used by clangd",
			"type": "shell",
			"command": "${workspaceFolder}/Engine/Binaries/DotNET/AutomationTool/UnrealBuildTool.exe",
			"args": [
				"-mode=GenerateClangDatabase",
				"-Project=\"F:/ProjectName/ProjectName.uproject\"",
				"-OutputDir=\"F:/ProjectName/\"",
				"-Filter=\".../ProjectName/Source/...\"",
				"ProjectNameEditor",
				"Development",
				"Win64"
			],
			"group": "build",
			"presentation": {
				"reveal": "always",
				"showReuseMessage": false
			},
			"promptOnClose": false,
			"problemMatcher": "$msCompile",
			"dependsOrder": "sequence",
			"dependsOn": ["Build UAT"]
		},
	]
}

```

After setting that up, you should be able to see your task and run the "Regenerate compile_commands.json for the Unreal Editor" task it by pressing `Ctrl+Shift+B` and picking it from the menu. After a little while (up to a couple minutes on my machine) it will pop a "compile_commands.json" on the workspace root, which is what we need (and right where we need it, clangd will search for it on the workspace root too). It will also create a bunch of ".rsp.gcd" files throughout the "Intermediate" folders of your target, that the "compile_commands.json" file includes.

It's important to note a few things, however:
- If you add a new source file to the Unreal Editor source, you need to run the task to describe how to compile it within "compile_commands.json", otherwise clangd will not work. This is analogous to the recommendation that you should run the "GenerateProjectFiles.bat" to update the VS solution;
- When those tasks are run, they will create and overwrite the ".rsp.gcd" files. UBT will pick up on this and want to rebuild/relink those objects, and so the next time you build you'll find your editor wants to recompile everything;
- If you delete your "Intermediate" folder to try "resetting things" for some reason, you will need to run this task again to recreate the ".rsp.gcd" files, or else clangd will not know anything about the types on the modules you modified;
- If you want to regenerate "compile_commands.json" for a subset of files, you can use the "-Filter" argument, which the third task above uses: You should run that task if you add any file to your project (here at "F:/ProjectName/ProjectName.uproject"). It will only touch that particular project's source files, so it won't recompile everything.

There are two more configuration bits you will need. First of all, place a ".clangd" file on your workspace and put this in it:
```
CompileFlags:
  Add: [-D__INTELLISENSE__, -ferror-limit=0]

Diagnostics:
  UnusedIncludes: Strict
```
These are how you pass additional definitions and arguments to clang while clangd is using it to compile your project internally. They come mostly from [this great forum post](https://forums.unrealengine.com/t/emacs-clangd-and-unreal-engine/246457/2) where user drcxd suggests these, as the `#ifdefs` around the `UCLASS` macro only really expand to something Intellisense/clangd can reason about in case `__INTELLISENSE__` is defined. As you can imagine, Intellisense defines that automatically while clangd does not, so we do that there.

The second bit of configuration left is to setup some settings for VSCode's clangd extension. There are many settings, but I think important ones are the below:
``` json
"clangd.arguments": [
  "-j=16",
  "--pch-storage=memory",
  "--clang-tidy",
  "--background-index"
]
```
We added this to our workspace settings already! This will have it build the background index and use up to 16 threads if it can. Keeping the PCH storage in memory supposedly helps with performance, and `--clang-tidy` is great for more analysis, although I believe it is enabled by default.

After you set this up clangd will start building the background index. On my mid-range PC for 2023, while it did run in the background it took between 6 and a 12 hours to complete while pinning my PC to 100% CPU usage, which was sort of crazy, although I haven't needed to do that again. This background index will live on the ".cache/" folder on the workspace root (which is why I excluded that folder on the workspace settings). It is possible that you do not need a background index and can just index on-demand, but I haven't compared the performance yet.

# Other tasks

Building, packaging, cooking and running UE are all done by directly interacting with UBT, and can be easily done via the command line (and so via VSCode tasks!). Here are a couple of useful things you may want to do. Note that these should just be additional entries on the `tasks` array in the "tasks.json". For clarity I'll omit the non-interesting part of the settings like `group`, `type` or `problemMatcher`, although keep in mind there are a [bunch](https://code.visualstudio.com/Docs/editor/tasks#_custom-tasks) in there.

### Building

Here are some basic tasks to build and lauch the editor by itself or with a project:

``` json
{
	"label": "Build Unreal Editor",
	"detail": "Just builds the Unreal Editor without specifying a project",
	"command": "${workspaceFolder}/Engine/Build/BatchFiles/Build.bat",
	"args": [
		"-Target=\"UnrealEditor Win64 Development\"",
		"-Target=\"ShaderCompileWorker Win64 Development\"",
		"-Quiet",
		"-WaitMutex",
		"-FromMsBuild"
	],
},
{
	"label": "Launch Unreal Editor",
	"detail": "Launch the Unreal Editor without a project",
	"command": "${workspaceFolder}/Engine/Binaries/Win64/UnrealEditor.exe",
},
{
	"label": "Build Project",
	"detail": "Actually builds the project's Editor target",
	"command": "${workspaceFolder}/Engine/Build/BatchFiles/Build.bat",
	"args": [
		"-Project=\"F:/ProjectName/ProjectName.uproject\"",
		"-Target=\"ProjectNameEditor Win64 Development\"",
		"-Target=\"ShaderCompileWorker Win64 Development\"",
		"-Quiet",
		"-WaitMutex",
		"-FromMsBuild"
	],
},
{
	"label": "Launch Project",
	"detail": "Launch the Unreal Editor for the provided project",
	"command": "${workspaceFolder}/Engine/Binaries/Win64/UnrealEditor.exe",
	"args": [
		"-Project=\"F:/ProjectName/ProjectName.uproject\"",
	],
},
```

### Updating .generated.h files

One of the first steps of the UE compilation process is that the Unreal Header Tool (UHT) parses your header files, like "file.h". If they have any of the UE macros in them (like `UCLASS`, `USTRUCT`, `UPROPERTY` and etc.), UHT will create a "file.generated.h" file with a ton of additional code, which clangd does need to read to provide sensible feedback.

Sometimes when these header files (like "file.h") are modified (say by adding new UPROPERTYs or modifying them), the contents of that file and "file.generated.h" can start to diverge, and clangd can start to spew some nonsense. You could run the full "Build Project" task for it, but a trick is that you can run it with the "-SkipBuild" argument to just have it update the ".generated.h" files instead. This only takes a few seconds, and can run in the background. Some people set this up to run every 5 minutes or after every save, but I just use a separate task for it:

``` json
{
	"label": "Regenerate headers",
	"detail": "Regenerate the .generated.h files in case you modify any headers",
	"command": "${workspaceFolder}/Engine/Build/BatchFiles/Build.bat",
	"args": [
		"-Target=\"ProjectNameEditor Win64 Development\"",
		"-Target=\"ShaderCompileWorker Win64 Development\"",
		"-Project=\"F:/ProjectName/ProjectName.uproject\"",
		"-SkipBuild"
	],
},
```

### Generating the Visual Studio solution

If for some reason you want to debug with VS instead of VSCode (we'll get to the debugging part later in the post though) you can use the following task to just regenerate the VS solution file anyway, launch it and debug with it. I wanted to add this because there are some potentially useful arguments you may not know about, which make this generation step slightly faster, and also prevent it from generating useless projects on the solution file.

``` json
{
	"label": "Generate project files",
	"detail": "Generate the Visual Studio solution file in case you want to use it for debugging",
	"command": "${workspaceFolder}/GenerateProjectFiles.bat",
	"args": [
		"ProjectName.uproject", // Just the project for this one target
		"-Game",
		"-NoIntellisense", // If we use VS, it will be just for debugging anyway
		"-NoShippingConfigs",
		"-CurrentPlatform", // Generates configurations for current platform only
		"-NoDotNet" // Prevents the generation of UnrealBuildTool and other C# projects
	],
},
```

### Full update

One thing that was useful for me was to setup a "full resync" task that I can run automatically at the end of the day/week to get UE ready for the next day. You can do that with something like this:
``` json
{
	"label": "Full resync",
	"detail": "Full update: Resyncs source control and builds everything",
	"dependsOrder": "sequence",
	"dependsOn": [
		"Resync source control",
		"Regenerate compile_commands.json for the Unreal Editor",
		"Regenerate compile_commands.json for Project",
		"Build Project",
		"Launch Project"
	]
}
```

I omitted the "Resync source control" for now, but you get the picture.

### Precompiling shaders

Note how I call the "Launch project" task at the end there. The intent is to get it to precompile the shaders that it will need to open the editor. With UE 5 this will only compile the shaders needed to *open the editor* though (i.e. assets used on your startup level). You may want a more shotgun approach and to have it compile all shaders and build all static meshes and so on. Apparently Epic [does something similar on a nightly basis](https://docs.unrealengine.com/5.1/en-US/derived-data-cache/#buildingderiveddata). You can use the following task for that, although keep in mind when I did this for a medium size project it took about 10 hours. I tried to restrict it only to the WindowsEditor platform, but to be perfectly honest I'm not sure if that has an effect or not.

``` json
{
	"label": "Fill derived data",
	"detail": "Compile shaders, builds meshes and does all the required one-time setup for your project so the editor opens fast",
	"command": "${workspaceFolder}/Engine/Binaries/Win64/UnrealEditor-Cmd.exe",
	"args": [
		"ProjectName",
		"-run=DerivedDataCache",
		"-targetplatform=WindowsEditor",
		"-fill"
	],
},
```

### Packaging and cooking

Finally, here is how you'd cook or package your project (packaging involves cooking):

``` json
{
	"label": "Package project",
	"detail": "Cooks and fully packages the project for target platform and configuration",
	"command": "${workspaceFolder}/RunUAT.bat",
	"args": [
		"-ScriptsForProject=\"F:/ProjectName/ProjectName.uproject\"",
		"BuildCookRun",
		"-project=\"F:/ProjectName/ProjectName.uproject\"",
		"-target=ProjectName",
		"-platform=Win64",
		"-clientconfig=Development",
		"-utf8output",
		"-nocompileeditor",
		"-skipbuildeditor",
		"-build",
		"-cook",
		"-stage",
		"-pak",
		"-archive",
		"-archivedirectory=\"C:/Output/Directory\""
	],
	"dependsOrder": "sequence",
	"dependsOn": ["Build UAT", "Build Project"]
},
{
	"label": "Cook content",
	"detail": "Cook content for a target platform and configuration",
	"command": "${workspaceFolder}/RunUAT.bat",
	"args": [
		"-ScriptsForProject=\"F:/ProjectName/ProjectName.uproject\"",
		"BuildCookRun",
		"-project=\"F:/ProjectName/ProjectName.uproject\"",
		"-target=ProjectName",
		"-platform=Win64",
		"-clientconfig=Development",
		"-utf8output",
		"-nocompileeditor",
		"-skipbuildeditor",
		"-cook",
	],
	"dependsOrder": "sequence",
	"dependsOn": ["Build UAT", "Build Project"]
},
```

These tasks are easy to construct on your own, or update to whatever arguments you use. Just launch the packaging/cooking task from the editor and keep an eye out on the Output Log: One of the first lines emitted will be the command and all required arguments to run your exact packaging/cooking task, which you can then extract and put it on a VSCode task.

The only thing I may add here is that I recommend having explicit dependencies on the UAT and "Build Project" tasks, as personally sometimes I forget to do this and it can lead to bizarre errors when trying to package.

# Clang-format

This is a great and very configurable code formatter for C++ (and a bunch of other languages) that also uses clang. There is an [extension for VSCode](https://marketplace.visualstudio.com/items?itemName=xaver.clang-format) you can install.

You can configure it with some pre-existing styles like Google or WebKit, or setup a custom style, which is what we'll do. For a custom style all you need to do is place a ".clang-format" file on your workspace root (and within each UE project's root!) with your chosen settings. That is usually enough for the extension to find it and use it, but there are some settings on the extension to have it point at a specific file path if you want.

I went over [Epic's coding standard](https://docs.unrealengine.com/5.1/en-US/epic-cplusplus-coding-standard-for-unreal-engine/) and all the different [clang-format options](https://clang.llvm.org/docs/ClangFormatStyleOptions.html), and found the values that best match. The standard itself is not very strict with the styling, but UE code has a distinct "look", which I tried to approach as much as possible. I used some references though, like [this one](https://github.com/ShifftC/UEClangFormat/blob/main/.clang-format), [this other one](https://github.com/TensorWorks/UE-Clang-Format) but especially [this one](https://gist.github.com/intinig/9bba3a3faee80250b781bf916a4ab8b7), that has an include category trick to put the generated files in the right position.

Here it is: [My .clang-format](https://github.com/1danielcoelho/UE-VSCode/blob/main/.clang-format)

# Debugging

It would be perfectly viable to debug using VS (by using the "Generate project files" task above and disabling Intellisense it's not that bad). You can keep it open in the background and just click the green play button to launch every time, but I really didn't want to have to keep two different editors open at all times.

Luckily the debugging workflow for C++ in VSCode is not so bad! And it has all the features I need, like data breakpoints and being able to easily see the callstacks of different threads. It's pretty easy to set it up: All you need is to place a "launch.json" file within the ".vscode" folder (so next to the "tasks.json" file we used earlier). Here is [the official documentation about it](https://code.visualstudio.com/Docs/editor/debugging#_launch-configurations). There are many other options like making configurations that attach to existing processes instead of launching them, and so on.

My full "launch.json" looks like this:

``` json
{
	"configurations": [
		{
			"name": "Build and debug",
			"type": "cppvsdbg",
			"request": "launch",
			"cwd": "${workspaceRoot}",
			"program": "${workspaceFolder}/Engine/Binaries/Win64/UnrealEditor.exe",
			"args": [
				"-project=\"F:/ProjectName/ProjectName.uproject\""
			],
			"internalConsoleOptions": "openOnSessionStart",
			"visualizerFile": "${workspaceFolder}/Engine/Extras/VisualStudioDebugging/Unreal.natvis",
			"console": "internalConsole",
			"preLaunchTask": "Build Project"
		}
	],
	"version": "2.0.0"
}
```

Note the `visualizerFile` entry: It points at the natvis file that ships with the engine, which is required in order to be able to inspect the UE types like `FString` in a usable manner. Luckily VSCode has a full implementation of the natvis handling stuff!

Also note that you can have a `preLaunchTask`, where you specify the `label` value for the task you want to run before launching the program. Unfortunately you can't easily pass any arguments or data between the launch configuration and the task... There are many issues on VSCode's GitHub page about this, but at the time of writing this is not yet supported. This means you'll need a separate launch/task pair if you want to test different platforms/configurations/project names/targets.

One other thing is that there is no easy way of using this launch configuration to "launch without debugging" for some reason, which is why I setup those dedicated tasks to do that instead!

Anyway, after this is setup you can switch VSCode to Run mode with `Ctrl+Shift+D` (or by clicking on View -> Run), and the "Build and debug" will show up as a configuration you can launch. Breakpoints, inspecting variables, stepping through callstacks and threads should work exactly the same as in VS.

# UE's default VSCode editor setup

Now that you have a full grasp of what I went for, you may want to know that it's possible to run the "GenerateProjectFiles.bat" file on the UE install with the "-VSCode" argument (you also get the same effect if you set VSCode as your source code editor on your UE Editor settings and then just run GenerateProjectFiles.bat with no arguments). This will automatically generate some "tasks.json" and "launch.json" files for your targets, which you may want to check out. Keep in mind that when you do this it will overwrite your existing files, so save your old "tasks.json" and "launch.json"!

I really disliked the output tasks and launch configurations from that command though, as it generates hundreds of different items for targets/configurations I don't really need, and doesn't generate the tasks I do actually want!

Setting VSCode as the source code editor on the UE Editor settings sadly also doesn't mean it can open VSCode whenever you want to e.g. see the source of a Blueprint node or open your project. It just doesn't really do anything for me at all in those situations.

# Step-by-step setup

Now that we know all the aspects involved, here is what you'd actually do if you want to set this up for yourself locally. I'm assuming you are building UE from the Github source, and don't have a UE project setup yet.

- Clone the Github source `git clone --single-branch --branch 5.2 https://github.com/EpicGames/UnrealEngine.git`;
- Run the contained "Setup.bat" to download the rest of the dependencies;
- Grab the files we described throughout this post from [my Github repo](https://github.com/1danielcoelho/UE-VSCode) or copy the desired snippets from this post;
- Open "Engine\Source\Runtime\Core\Public\GenericPlatform\GenericPlatformProcess.h" and change the line 816 (as of UE 5.2) from this:
``` C++
#	error Unsupported architecture!
```
Into this:
``` C++
#   ifndef __INTELLISENSE__
#	    error Unsupported architecture!
#   endif
```
If you don't do this, this "Unsupported architecture!" error will show up on almost every file... This change just prevents the error from showing up as a problem *for clangd*, but it won't affect anything else. We don't really care about the missing "pause" intrinsics for clangd's build as it won't actually be run anyway!
- Run the "Build Unreal Editor" target (by pressing `Ctrl+Shift+B` in VSCode and picking from the list);
- Run the "Launch Unreal Editor" target to open the UE project picker and create a new project;
- Add your new project as a folder to your VSCode workspace if you want (by right-clicking open space on the exporer view in VSCode);
- Rename the "ProjectName" instances to your actual project name and path within "tasks.json" and "launch.json";
- Run the "Regenerate compile_commands.json for the Unreal Editor" task;
- Run the "Regenerate compile_commands.json for Project" task;
- Run the "Build Project" task.

That's it! Everything should be working now. From now you can run the "Launch Project" task to just launch it without debugging, or launch the debugging configuration we talked about on [the Debugging section](#debugging).

Here's how the rest of the workflow works:

- You can modify files on the project source freely, and just hit Recompile (or enable Live Coding) in the editor to hot reload the changes;
- Any time you modify a header file too much, you need to either rebuild or run the "Regenerate headers" task, or clangd will start generating garbage;
- Any time you add a new source file to your project, you may need to run the "Regenerate compile_commands.json for Project" task (sometimes clangd can go a long time without needing this, somehow);
- Any time you add a new source file to the UE source, you may need to run the "Regenerate compile_commands.json for Unreal Editor" task.

# Comparisons with VS

After using it for a few weeks, I can safely say this is a superior workflow (for me!). I don't think I'll be going back any time soon, but here are some bullet points:

The good:
- VSCode opens instantly and feels overall much snappier to use than VS (low bar though);
- Clangd with clang-tidy is great at spotting things like unused variables or includes, and you can e.g. set up your ".clangd" file to use something like "-Wall" and other flags to get as much feedback as you want;
- It works great with other VSCode extensions like "Error lens", which can show the error messages directly inline with your code;
- Opening a file shows the basic regex-based syntax highlighting instantly, and after clangd finishes loading the index for a file (or building it) it shows the proper, AST-based highlighing, which seems to stay loaded in memory for the whole session. On VS even after giving VS Intellisense 32GB of RAM to work with, after switching through a handful of files it will drop the index for a previous file. Opening an unindexed file on VS Intellisense will just show absolutely no syntax highlighing of any kind;
- "Go to definition" works really well, and it's quite interesting to do it on a macro and see where it goes. I work with third-party libraries as well, and it can index into them no problem;
- Having all of these custom tasks setup and a couple keystrokes away is great. I work with multiple projects at a time so it's great to be working on one and start packaging this other project instantly without having to change "solution files" or anything of the sort.
- I like that the clangd error messages come from clang, and if you build on Windows you'll usually end up using MSVC. This means you're checking your code with two compilers, so that's a higher chance of catching errors.

The bad:
- Not exactly straightforward (look how long this blog post is, for starters);
- For some reason it's sometimes bad at finding the header/cpp file pairs? You'll have file.h and file.cpp open and indexed, and doing the shortcut to switching between Source/Header will send me to "ObjectMacros.h" or somewhere bizarre?
- Building the clangd background index takes a ridiculous amount of time. I don't have any comparisons with the performance with it enabled or disabled though, so maybe that's worth investigating;
- When right-clicking a Blueprint node and picking to show the C++ implementation, UE will default to opening the VS solution file (which doesn't exist) and show an error toast instead. I haven't tried configuring this yet though;
- Searching for files by name takes a bit longer than VS for some reason (although it does seem to cache these afterwards). I've tried restricting the file search on the workspace settings but it's still slow;
- I've noticed that the debugger takes a while longer to load local variables sometimes, and so stepping through code can be slower than in VS (believe it or not);
- The VSCode debugger interface doesn't have a "run program up to this line" feature. I remember laughing at this feature when VS released it (as you can achieve the same by setting a new breakpoint, hiting Continue, and then removing it) but I actually miss it;
- Once every couple of days clangd shows some incorrect analysis for a file, like it failed to parse something, and it won't go away until I close the file and open it again;
- It takes a comparable amount of time to parse a file compared to Intellisense for me. It's not bad per se, just disappointing. This is not so bad as it seems to retain that in memory for way longer than VS Intellisense however;

# Conclusions and next steps

If you scrolled down here and missed it, here is [my Github repo](https://github.com/1danielcoelho/UE-VSCode) with everything described in this blog post. You can mostly copy-and-paste those files onto an UE (from Github) installation and be good to go.

Overall, if you prefer VSCode I'd say this approach is worth it. It doesn't take that long to setup: This article is really just this long because I'm very bad at summarizing.

There are many things I want to improve with this, for example:
- Make a more seamless "first setup" task/script to setp all this up;
- Somehow find a way of not having to spell out the UE project's path and target for every single task... there are ways using environment variables/env files/other extensions, but they all seemed to just add too much more complication into the mix;
- Find a way of having UE properly call into the open VSCode workspace when it wants to show source code for whatever reason;
- I believe there must be ways of making the clangd parsing faster by tweaking it's compilation on the ".clangd" file, although I haven't tried that much just yet.

But for now, this should be all I wanted to show about my current setup. Hopefully this helps you with yours!

Thanks for reading!