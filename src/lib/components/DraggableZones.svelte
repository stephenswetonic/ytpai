<script>
    import Sortable, { MultiDrag } from "sortablejs";
    import { onMount, afterUpdate } from "svelte";
    import wordJsonSample from "$lib/wordJsonSample.json";

    export let chosenWords = [];
    let generatedWords = [];
    let groupedWords = {};
    let matchedWords = [];
    let chosenWordsContainer;
    let matchedWordsContainer;
    let inputText;

    onMount(() => {
        Sortable.mount(new MultiDrag());
        createChosenWordsSortable();
    });

    afterUpdate(() => {
        createGroupSortables();
        createMatchedWordsSortable();
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
                scroll: true,
                forceAutoScrollFallback: false,
                scrollSensitivity: 50,
                scrollSpeed: 10,
                bubbleScroll: true,

                onEnd: (evt) => {
                    handleDragEnd(
                        evt,
                        chosenWords,
                        groupedWords[evt.from.dataset.group],
                    );
                },
            });
        }
    }

    function createMatchedWordsSortable() {
        if (matchedWordsContainer) {
            Sortable.create(matchedWordsContainer, {
                group: {
                    name: "foo",
                    put: false,
                    pull: "clone",
                },
                direction: "horizontal",
                delay: 200,
                delayOnTouchOnly: true,
                multiDrag: true,
                selectedClass: "selected",
                scroll: true,
                forceAutoScrollFallback: false,
                scrollSensitivity: 50,
                scrollSpeed: 10,
                bubbleScroll: true,

                //not needed?
                onEnd: (evt) => {
                    handleDragEnd(evt, matchedWords, chosenWords);
                },
            });
        }
    }

    function createGroupSortables() {
        Object.keys(groupedWords).forEach((key) => {
            const container = document.querySelector(`.container-${key}`);
            // @ts-ignore
            if (container && !container.sortableInstance) {
                Sortable.create(container, {
                    group: {
                        name: "foo",
                        put: false,
                        pull: "clone",
                    },
                    direction: "horizontal",
                    delay: 200,
                    delayOnTouchOnly: true,
                    multiDrag: true,
                    selectedClass: "selected",
                    scroll: true,
                    forceAutoScrollFallback: false,
                    scrollSensitivity: 50,
                    scrollSpeed: 10,
                    bubbleScroll: true,

                    //not needed?
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
    }

    function moveItems(fromList, toList, evt) {
        const movedItems = evt.items.map((item) => {
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
            if (movedItems[ix]) toList.splice(insertIndex, 0, movedItems[ix]);
        });
    }

    export function fillWords(words) {
        generatedWords = words;
        groupedWords = groupWordsByTime(generatedWords, 10);
        createGroupSortables();
    }

    function fillFromJson() {
        generatedWords = wordJsonSample;
        groupedWords = groupWordsByTime(generatedWords, 10);
        createGroupSortables();
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

    function addWordsFromInput() {
        const wordArray = inputText.toLowerCase().split(" ");

        let intersection = generatedWords.filter((x) =>
            wordArray.includes(x.word.toLowerCase()),
        );

        matchedWords = intersection;
    }

    function clearChosenWords() {
        chosenWords = [];
        chosenWords = [...chosenWords];
        while (chosenWordsContainer.lastElementChild) {
            chosenWordsContainer.removeChild(
                chosenWordsContainer.lastElementChild,
            );
        }
    }
</script>

{#if generatedWords.length > 0}
    <h1 class="mt-2 text-xl font-bold tracking-light text-base-content">
        Generated Words
    </h1>
    <div class="generatedWords border border-white rounded-lg">
        {#each Object.keys(groupedWords) as key}
            <div
                class="container horizontal container-{key} mb-2"
                data-group={key}
            >
                {#each groupedWords[key] as listItem, i (listItem.id)}
                    <p class="draggable rounded bg-gray-800" data-index={i}>
                        {listItem.word}
                    </p>
                {/each}
            </div>
        {/each}
    </div>

    <input
        class="input w-full max-w-xl bg-base-200 my-2"
        bind:value={inputText}
        type="text"
        placeholder="Type here"
    />
    <button class="btn btn-primary" on:click={addWordsFromInput}>Filter</button>

    <h1 class="mt-2 text-xl font-bold tracking-light text-base-content">
        Matched Words
    </h1>

    <div class="matchedWords border border-white rounded-lg">
        <div class="container horizontal" bind:this={matchedWordsContainer}>
            {#each matchedWords as listItem, i (listItem.id)}
                <p class="draggable rounded bg-gray-800" data-index={i}>
                    {listItem.word}
                </p>
            {/each}
        </div>
    </div>
{:else}
    <div></div>
{/if}

<h1
    class="mt-2 text-xl font-bold tracking-light text-base-content inline-block"
>
    Words To Mix
</h1>

<button class="btn btn-sm btn-primary m-1" on:click={clearChosenWords}
    >Clear</button
>

<div class="chosenWords border border-white rounded-lg">
    <div class="container horizontal" bind:this={chosenWordsContainer}>
        {#each chosenWords as listItem, i (listItem.id)}
            <p class="draggable rounded bg-gray-800" data-index={i}>
                {listItem.word}
            </p>
        {/each}
    </div>
</div>

<style>
    :global(.sortable-ghost) {
        opacity: 25%;
    }

    :global(.selected) {
        box-sizing: border-box;
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
        box-shadow: 0px 1px 1px 0 rgb(0 0 0 / 10%);
        display: flex;
        flex-wrap: wrap;
    }

    .container.horizontal {
        flex-direction: row;
    }

    .container.horizontal .draggable {
        margin-right: 0.25em;
    }

    .chosenWords .container.horizontal {
        padding: 15px;
    }

    .matchedWords .container.horizontal {
        padding: 15px;
    }

    .draggable {
        box-sizing: border-box;
        color: #fff;
        padding: 0.1em 0.25em;
        margin: 0.1em;
        cursor: pointer;
        border-left: 1px solid transparent;
    }
</style>
