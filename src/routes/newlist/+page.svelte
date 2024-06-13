<script>
    import { Sortable, MultiDrag } from "sortablejs";
    import { onMount, afterUpdate } from "svelte";
    import wordJsonSample from "$lib/wordJsonSample.json";

    let generatedWords = [];
    let chosenWords = [];
    let groupedWords = {};
    let selectedIds = [];
    let chosenWordsContainer;

    onMount(() => {
        Sortable.mount(new MultiDrag());
        createChosenWordsSortable();
    });

    afterUpdate(() => {
        createGroupSortables();
    });

    function createChosenWordsSortable() {
        if (chosenWordsContainer) {
            Sortable.create(chosenWordsContainer, {
                group: {
                    name: "foo",
                    put: true,
                },
                direction: "horizontal",
                delay: 200,
                delayOnTouchOnly: true,

                multiDrag: true,
                selectedClass: "selected",

                onEnd: (evt) => {
                    handleDragEnd(evt, chosenWords, groupedWords[evt.from.dataset.group]);
                },
            });
        }
    }

    function createGroupSortables() {
        Object.keys(groupedWords).forEach(key => {
            const container = document.querySelector(`.container-${key}`);
            // @ts-ignore
            if (container && !container.sortableInstance) {
                Sortable.create(container, {
                    group: {
                        name: "foo",
                        put: false,
                    },
                    direction: "horizontal",
                    delay: 200,
                    delayOnTouchOnly: true,

                    multiDrag: true,
                    selectedClass: "selected",

                    onEnd: (evt) => {
                        handleDragEnd(evt, groupedWords[key], chosenWords);
                    },
                });
                // @ts-ignore
                container.sortableInstance = true; // Mark container as having sortable instance
            }
        });
    }

    function handleDragEnd(evt, fromList, toList) {
        const fromGroup = evt.from.dataset.group;
        const toGroup = evt.to.dataset.group;

        if (fromGroup !== undefined && toGroup !== undefined) {
            fromList = groupedWords[fromGroup];
            toList = groupedWords[toGroup];
        } else if (fromGroup === undefined && toGroup !== undefined) {
            fromList = chosenWords;
            toList = groupedWords[toGroup];
        } else if (fromGroup !== undefined && toGroup === undefined) {
            fromList = groupedWords[fromGroup];
            toList = chosenWords;
        }

        moveItems(fromList, toList, evt);

        // Log the lists for debugging
        console.log("Grouped Words:", groupedWords);
        console.log("Chosen Words:", chosenWords);
    }

    function moveItems(fromList, toList, evt) {
        const movedItems = evt.items.map(item => {
            const index = item.dataset.index;
            return fromList[index];
        });

        // Remove moved items from the original list
        for (let i = movedItems.length - 1; i >= 0; i--) {
            const index = evt.oldIndicies[i].index;
            fromList.splice(index, 1);
        }

        // Insert moved items into the new list at the appropriate position
        evt.newIndicies.forEach((el, ix) => {
            const insertIndex = evt.newIndex + ix;
            toList.splice(insertIndex, 0, movedItems[ix]);
        });
    }

    function fillWords() {
        generatedWords = wordJsonSample;
        groupedWords = groupWordsByTime(generatedWords, 10);
        createGroupSortables(); // Ensure Sortable instances are created after filling words
    }

    function groupWordsByTime(words, interval) {
        return words.reduce((acc, word) => {
            const groupKey = Math.floor(word.start / interval) * interval;
            if (!acc[groupKey]) {
                acc[groupKey] = [];
            }
            acc[groupKey].push(word);
            return acc;
        }, {});
    }

    function logLists() {
        console.log("Generated Words:", generatedWords);
        console.log("Chosen Words:", chosenWords);
    }

    function logSelected() {
        console.log("Selected IDs:", selectedIds);
    }
</script>

<button class="btn btn-primary" id="fillWords" on:click|stopPropagation={fillWords}>
    Fill words
</button>

<button class="btn btn-primary" on:click={logLists}>
    Log lists
</button>

<button class="btn btn-primary" on:click={logSelected}>
    Log selected
</button>

<div class="generatedWords">
    {#each Object.keys(groupedWords) as key}
        <div class="container horizontal container-{key}" data-group={key}>
            {#each groupedWords[key] as listItem, i (listItem.id)}
                <p class="draggable" data-index={i}>{listItem.word}</p>
            {/each}
        </div>
    {/each}
</div>

<div class="chosenWords">
    <div class="container horizontal" bind:this={chosenWordsContainer}>
        {#each chosenWords as listItem, i (listItem.id)}
            <p class="draggable" data-index={i}>{listItem.word}</p>
        {/each}
    </div>
</div>

<style>
    :global(.sortable-ghost) {
        opacity: 25%;
    }

    :global(.selected) {
        font-weight: bold;
        border-left: 1px solid #ff3e00 !important;
        box-shadow: 0px 5px 5px 0 rgb(0 0 0 / 10%);
    }

    .chosenWords {
        display: flex;
        flex-direction: column;
    }

	.generatedWords {
		display: flex;
        flex-direction: column;
	}

    .container {
        background-color: white;
        border: 1px solid white;
        margin: 0.25em;
        padding: 0.5em;
        min-width: 250px;
        border-radius: 10px;
        box-shadow: 0px 1px 1px 0 rgb(0 0 0 / 10%);
        transition: all 0.2s;
        display: flex;
        flex-wrap: wrap;
    }

    .container.horizontal {
        flex-direction: row;
    }

    .container.horizontal .draggable {
        margin-right: 0.25em;
    }

    .container .draggable:first-child {
        border-top-left-radius: 0.25rem;
        border-top-right-radius: 0.25rem;
    }
    .container .draggable:last-child {
        border-bottom-left-radius: 0.25rem;
        border-bottom-right-radius: 0.25rem;
    }

	.chosenWords .container.horizontal {
		min-height: 50px;
	}

    .draggable {
        color: #333;
        background-color: white;
        border: 1px solid #eee;
        padding: 0.1em 0.25em;
        margin: -1px;
        cursor: pointer;
    }

    .draggable:hover {
        background-color: #fafafa;
    }
</style>
